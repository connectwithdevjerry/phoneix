import ee

def ensure_gee_initialized():
    try:
        ee.Authenticate(auth_mode='web')
        ee.Initialize()
    except Exception as e:
        # return
        # raise RuntimeError(f"GEE failed: {e}\nRun: earthengine authenticate") from e
        pass

ensure_gee_initialized()

# 1. ROI (Nigeria)
# ===============================
nigeria = (ee.FeatureCollection("FAO/GAUL/2015/level0")
           .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria')))

roi = nigeria.geometry()
# ===============================
# 2. DATASETS & PARAMETERS
# ===============================
time_start = '2001-01-01'
time_end   = '2024-01-01'

# Load MODIS NDVI
ndvi = (ee.ImageCollection("MODIS/061/MOD13A2")
        .select('NDVI')
        .filterBounds(roi)
        .filterDate(time_start, time_end))

# Load MODIS LST (Day)
lst = (ee.ImageCollection("MODIS/061/MOD11A2")
       .select('LST_Day_1km')
       .filterBounds(roi)
       .filterDate(time_start, time_end))

# NDVI MIN / MAX (Global statistics for the period)
# Scaling 0.0001 per MODIS docs
ndvi_min = ndvi.min().multiply(0.0001)
ndvi_max = ndvi.max().multiply(0.0001)

# LST MIN / MAX (Global statistics for the period)
# Scaling 0.02 per MODIS docs
lst_min = lst.min().multiply(0.02)
lst_max = lst.max().multiply(0.02)

# ===============================
# 3. TEMPORAL MEDIAN FUNCTION
# ===============================
def temporal_collection(collection, start_date, count, interval, unit):
    seq = ee.List.sequence(0, ee.Number(count).subtract(1))
    origin = ee.Date(start_date)

    def get_median(i):
        start = origin.advance(ee.Number(i).multiply(interval), unit)
        end = origin.advance(ee.Number(i).add(1).multiply(interval), unit)
        return (collection
                .filterDate(start, end)
                .median() # Median avoids nulls/clouds often
                .set('system:time_start', start.millis()))

    return ee.ImageCollection(seq.map(get_median))

# Create Monthly Collections (276 months approx for 23 years)
ndvi_monthly = temporal_collection(ndvi, time_start, 276, 1, 'month')
lst_monthly  = temporal_collection(lst,  time_start, 276, 1, 'month')

# ===============================
# 4. CALCULATE INDICES (VCI, TCI, VHI)
# ===============================

# VCI — Vegetation Condition Index
def calculate_vci(img):
    index = img.expression(
        '(ndvi - min) / (max - min)',
        {
            'ndvi': img.select('NDVI').multiply(0.0001),
            'min':  ndvi_min,
            'max':  ndvi_max
        }
    )
    return index.rename('VCI').copyProperties(img, img.propertyNames())

vci = ndvi_monthly.map(calculate_vci)

# TCI — Thermal Condition Index
# Formula: (Max - LST) / (Max - Min)
def calculate_tci(img):
    index = img.expression(
        '(max - lst) / (max - min)',
        {
            'max': lst_max,
            'min': lst_min,
            'lst': img.select('LST_Day_1km').multiply(0.02)
        }
    )
    return index.rename('TCI').copyProperties(img, img.propertyNames())

tci = lst_monthly.map(calculate_tci)

# Combine VCI and TCI to calculate VHI
# Join them based on system:time_start (assuming they align monthly)
filter_time = ee.Filter.equals(leftField='system:time_start', rightField='system:time_start')
join = ee.Join.saveFirst('match')
modis_indices = ee.ImageCollection(join.apply(vci, tci, filter_time))

def calculate_vhi(img):
    tci_img = ee.Image(img.get('match')) # Get the matched TCI image
    vhi = img.expression(
        '0.5 * vci + 0.5 * tci',
        {
            'vci': img.select('VCI'),
            'tci': tci_img.select('TCI')
        }
    ).rename('VHI')
    return img.addBands(vhi).copyProperties(img, img.propertyNames())

drought = modis_indices.map(calculate_vhi)

# ===============================
# 5. RISK CLASSIFICATION
# ===============================
def classify_risk(img):
    risk = img.select('VHI').expression(
        "(vhi < 0.1) ? 4" +
        ": (vhi < 0.2) ? 3" +
        ": (vhi < 0.4) ? 2" +
        ": (vhi < 0.6) ? 1" +
        ": 0",
        {'vhi': img.select('VHI')}
    ).rename('DROUGHT_CLASS')
    return img.addBands(risk)

drought_classified = drought.map(classify_risk)

# ===============================
# 6. VISUALIZATION (Example Year: 2015)
# ===============================
vhi_2015 = (drought_classified
            .filterDate('2015-01-01', '2015-12-31')
            .mean()
            .clip(roi))

vis = {
    'min': 0, 'max': 4,
    'palette': ['green', 'yellow', 'orange', 'red', 'purple']
}

# ===============================
# 7. INTERACTIVE CLICK EVENT
# ===============================
def droughtAnalysis(lat, lon):
    drought = "Drought analysis: "
    if lat is None or lon is None:
        return {"message": drought + "Kindly provide valid latitude and longitude."}

    point = ee.Geometry.Point([lon, lat])

    try:
        # Sample the VHI 2015 layer
        sampled = (vhi_2015.sample(region=point, scale=500, numPixels=1, geometries=True)
                   .first())

        # FIX: Check if sampled is valid immediately
        if sampled is None:
            print(f"Clicked ({lat:.4f}, {lon:.4f}): No data (masked).")
            return

        result = sampled.getInfo()

        if result is None or 'properties' not in result:
             print(f"Clicked ({lat:.4f}, {lon:.4f}): No properties found.")
             return

        props = result['properties']
        vhi = props.get('VHI')
        klass = props.get('DROUGHT_CLASS')

        if vhi is None or klass is None:
             print("Data is None at this pixel.")
             return {"message": drought + "Data is None at this pixel."}

        labels = {
            4: "Extreme Drought",
            3: "Severe Drought",
            2: "Moderate Drought",
            1: "Mild Drought",
            0: "No Drought"
        }

        print("--------------------------")
        print(f"📍 Location: {lat:.4f}, {lon:.4f}")
        print(f"VHI Score: {vhi:.3f}")
        print(f"Status: {labels.get(int(klass), 'Unknown')}")
        print("--------------------------")

        return {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "VHI": f"{vhi:.3f}",
            "Drought_Class": labels.get(int(klass), "Unknown"),
            "message": ""
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"message": drought + "An error occurred while processing the position data."}