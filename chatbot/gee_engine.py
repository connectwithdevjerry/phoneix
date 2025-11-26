# chatbot/gee_engine.py
import ee
from ee import EEException
from django.conf import settings

# === GLOBALS (built once) ===
countries = None
nigeria = None
fsi_class = None
vhi_2015 = None
lst_class = None

def ensure_gee_initialized():
    try:
        ee.Authenticate(auth_mode='web')
        ee.Initialize()
    except Exception as e:
        # return
        # raise RuntimeError(f"GEE failed: {e}\nRun: earthengine authenticate") from e
        pass

ensure_gee_initialized()
# ===============================
# ROI (Nigeria)
# ===============================
roi = (ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
       .filter(ee.Filter.eq('country_na', 'Nigeria')))

# ===============================
# CONSTANTS
# ===============================
lambda_const = 10.895e-6  # Wavelength (m)
rho = 1.438e-2            # Constant (m·K)

# ===============================
# LANDSAT 8 COLLECTION
# ===============================
l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

# Apply scaling
def applyScaleFactors(image):
    opticalBands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
    thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return (image.addBands(opticalBands, overwrite=True)
                 .addBands(thermalBands, overwrite=True))

l8 = l8.map(applyScaleFactors)

# Visualization
visualization = {
    'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
    'min': 0.0,
    'max': 0.3,
}

# ===============================
# 2025 IMAGE
# ===============================
image_25 = (l8.filterBounds(roi)
              .filterDate("2023-01-01", "2025-12-31")
              .filterMetadata("CLOUD_COVER", "less_than", 10)
              .median()
              .clip(roi))

# ===============================
# NDVI
# ===============================
ndvi_25 = image_25.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI_25')

# NDVI min & max
min_ndvi_25 = ee.Number(
    ndvi_25.reduceRegion(
        reducer=ee.Reducer.min(),
        geometry=roi,
        scale=100,
        maxPixels=1e9
    ).get('NDVI_25')
)

max_ndvi_25 = ee.Number(
    ndvi_25.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=roi,
        scale=100,
        maxPixels=1e9
    ).get('NDVI_25')
)

# ===============================
# EMISSIVITY
# ===============================
pv_25 = (ndvi_25.subtract(min_ndvi_25)
              .divide(max_ndvi_25.subtract(min_ndvi_25))
              .pow(2)
              .rename('PV_25'))

emissivity_25 = pv_25.multiply(0.004).add(0.986).rename('Emissivity_25')

# ===============================
# LAND SURFACE TEMPERATURE (LST)
# ===============================
thermal_25 = image_25.select('ST_B10')

lst_25 = (thermal_25.expression(
            '(BT) / (1 + (lambda * BT / rho) * log(emissivity))',
            {
                'BT': thermal_25,
                'lambda': lambda_const,
                'rho': rho,
                'emissivity': emissivity_25
            })
          .subtract(273.15)
          .rename('LST_25'))

# ===============================
# CLASSIFY LST INTO HEAT CATEGORIES
# ===============================

lst_class = (lst_25
    .where(lst_25.gte(23).And(lst_25.lt(30)), 1)
    .where(lst_25.gte(30).And(lst_25.lt(34)), 2)
    .where(lst_25.gte(34).And(lst_25.lt(38)), 3)
    .where(lst_25.gte(38).And(lst_25.lt(42)), 4)
    .where(lst_25.gte(42).And(lst_25.lte(48)), 5)
    .rename('Heat_Class')
)

visClass = {
    'min': 1,
    'max': 5,
    'palette': ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c']
}

# ===============================
# INTERACTIVE MAP CLICK EVENT
# ===============================
def lstAnalysis(lat, lon):
    point = ee.Geometry.Point([lon, lat])

    sampled = (lst_25.addBands(lst_class)
               .sample(region=point, scale=100, numPixels=1, geometries=True)
               .first())

    if sampled is None:
        print("No data for this point.")
        return

    result = sampled.getInfo()
    props = result['properties']

    temp = props.get('LST_25')
    cls = int(props.get('Heat_Class'))

    labels = {
        1: "Comfortable Warmth",
        2: "Mildly Elevated",
        3: "High (or Warm)",
        4: "Very High (or Hot)",
        5: "Extreme Heat"
    }

    print("Clicked point:", (lat, lon))
    print("LST (°C):", temp)
    return {"Category": labels.get(cls, "No data"), "Temperature (°C)": round(temp, 2), "Latitude": lat, "Longitude": lon}
