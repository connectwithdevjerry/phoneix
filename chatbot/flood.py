import base64
import json
import os
import ee
from .gee_engine import ensure_gee_initialized

ensure_gee_initialized()

# Study area, Nigeria as a country
countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
nigeria = countries.filter(ee.Filter.eq('country_na', 'Nigeria'))

# ==========================================
# 2. DEM (SRTM 30m)
# ==========================================
dem = ee.Image('USGS/SRTMGL1_003').clip(nigeria)

# ==========================================
# 3. SLOPE
# ==========================================
slope = ee.Terrain.slope(dem)

# ==========================================
# 4. HYDROSHEDS (Flow Accumulation)
# ==========================================
# Defining standard HydroSHEDS dataset ID
hydrodataset = ee.Image("WWF/HydroSHEDS/30ACC")
flowAccumulation = hydrodataset.select('b1').clip(nigeria)

# ==========================================
# 5. DISTANCE TO RIVERS
# ==========================================
riverMask = flowAccumulation.gt(1000) # Threshold
scale = flowAccumulation.projection().nominalScale()

riverDistance = (riverMask.fastDistanceTransform(30)
                 .sqrt()
                 .multiply(scale)
                 .clip(nigeria))

# ==========================================
# 6. LANDCOVER (ESA WorldCover)
# ==========================================
lulc = ee.Image('ESA/WorldCover/v200/2021').clip(nigeria)

# ==========================================
# 7. CHIRPS RAINFALL (2018–2025)
# ==========================================
chirps = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
          .filterDate('2018-01-01', '2025-12-31')
          .filterBounds(nigeria))

# Compute mean annual rainfall
years = ee.List.sequence(2018, 2025)

def get_annual_rain(y):
    yearly = chirps.filter(ee.Filter.calendarRange(y, y, 'year')).sum()
    return yearly.set('year', y)

annualRain = ee.ImageCollection.fromImages(years.map(get_annual_rain))
meanAnnualRain = annualRain.mean().clip(nigeria)

# ==========================================
# 8. SENTINEL-2 (NDVI & NDWI)
# ==========================================
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate('2021-01-01', '2025-12-31')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

s2_median = s2.median().clip(nigeria)

# ==========================================
# 10. SOIL DATA (SoilGrids)
# ==========================================
soildataset = ee.Image('ISRIC/SoilGrids250m/v2_0/wv0010').select('val_0_5cm_Q0_95')
soilNigeria = soildataset.clip(nigeria)

# ==========================================
# 11 & 12. NDVI & NDWI
# ==========================================
ndvi = s2_median.normalizedDifference(['B8', 'B4']).rename('NDVI')
ndwi = s2_median.normalizedDifference(['B3', 'B8']).rename('NDWI')

# ==========================================
# 15. PREPROCESSING & NORMALIZATION
# ==========================================

# 15a. Normalize DEM (Inverted: Low Elevation = High Risk)
dem_norm = dem.unitScale(0, 1000)
dem_inv = ee.Image(1).subtract(dem_norm)

# 15b. Normalize Slope (Inverted: Flat = High Flood Risk)
slope_norm = slope.unitScale(0, 30)
slope_inv = ee.Image(1).subtract(slope_norm)

# 15c. Normalize Rainfall
rain_norm = meanAnnualRain.unitScale(500, 3000)

# 15d. Normalize Flow Accumulation (Log Scale)
flow_log = flowAccumulation.add(1).log()

# Calculate max flow for scaling (Server-side calculation)
max_flow = flow_log.reduceRegion(
    reducer=ee.Reducer.max(),
    geometry=nigeria,
    scale=1000, # Increased scale slightly for speed
    maxPixels=1e13
).values().get(0)

flow_norm = flow_log.unitScale(0, max_flow)

# 15e. Normalize NDVI (Inverted: Low Veg = High Runoff/Risk)
ndvi_norm = ndvi.unitScale(0, 1)
ndvi_inv = ee.Image(1).subtract(ndvi_norm)

# 15f. Normalize Soil
soil_norm = soilNigeria.unitScale(-0.06, 0.63)

# 15g. LULC Reclassification
# Note: Python lists [ ] instead of JS arrays
lulc_floodrisk = lulc.remap(
    [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
    [0.2, 0.4, 0.6, 0.8, 0.9, 0.7, 0.3, 0.1, 0.5, 0.5, 0.6]
).rename('LULC_FloodRisk')

# 15h. Normalize River Distance (Inverted: Close to river = High Risk)
riverDist_norm = riverDistance.unitScale(0, 5000)
riverDist_inv = ee.Image(1).subtract(riverDist_norm)

# ==========================================
# 16. LAYER STACK
# ==========================================
normStack = ee.Image.cat([
    dem_inv.rename('dem_inv'),
    slope_inv.rename('slope_inv'),
    rain_norm.rename('rain_norm'),
    flow_norm.rename('flow_norm'),
    ndvi_inv.rename('ndvi_inv'),
    lulc_floodrisk.rename('lulc'),
    soil_norm.rename('soil_norm'),
    riverDist_inv.rename('riverDist_inv')
]).clip(nigeria)

# ==========================================
# 18 & 19. AHP CALCULATION
# ==========================================
weights = {
    'flow_norm': 0.30999795,
    'riverDist_inv': 0.20715768,
    'rain_norm': 0.12015950,
    'slope_inv': 0.07692779,
    'dem_inv': 0.15348581,
    'soil_norm': 0.04972386,
    'lulc': 0.04972386,
    'ndvi_inv': 0.03282355
}

fsi_ahp = (normStack.select('flow_norm').multiply(weights['flow_norm'])
    .add(normStack.select('riverDist_inv').multiply(weights['riverDist_inv']))
    .add(normStack.select('rain_norm').multiply(weights['rain_norm']))
    .add(normStack.select('slope_inv').multiply(weights['slope_inv']))
    .add(normStack.select('dem_inv').multiply(weights['dem_inv']))
    .add(normStack.select('soil_norm').multiply(weights['soil_norm']))
    .add(normStack.select('lulc').multiply(weights['lulc']))
    .add(normStack.select('ndvi_inv').multiply(weights['ndvi_inv']))
    .clip(nigeria))

# ==========================================
# 20. PERCENTILE CLASSIFICATION
# ==========================================
fsi_named = fsi_ahp.rename('FSI_AHP').unmask(0)

# Calculate percentiles (This step is computationally heavy)
fsiPercentiles = fsi_named.reduceRegion(
    reducer=ee.Reducer.percentile([20, 40, 60, 80]),
    geometry=nigeria,
    scale=1000, # Increased scale to prevent Timeouts in Colab
    tileScale=4,
    maxPixels=1e13
)

# Get values as EE Numbers
p20 = ee.Number(fsiPercentiles.get('FSI_AHP_p20'))
p40 = ee.Number(fsiPercentiles.get('FSI_AHP_p40'))
p60 = ee.Number(fsiPercentiles.get('FSI_AHP_p60'))
p80 = ee.Number(fsiPercentiles.get('FSI_AHP_p80'))

# Classification Expression
fsi_class = fsi_named.expression(
    "(fsi <= p20) ? 1" +
    " : (fsi <= p40) ? 2" +
    " : (fsi <= p60) ? 3" +
    " : (fsi <= p80) ? 4" +
    " : 5",
    {
        'fsi': fsi_named,
        'p20': p20,
        'p40': p40,
        'p60': p60,
        'p80': p80
    }
).rename('Susceptibility_Class')

# Visualization
classVis = {
    'min': 1,
    'max': 5,
    'palette': ['red', 'orange', 'yellow', 'cyan', 'blue']
}

# ==========================================
# INTERACTIVE CLICK EVENT (With Error Fix)
# ==========================================
def floodAnalysis(lat, lon):
    if lat is None or lon is None:
        return

    point = ee.Geometry.Point([lon, lat])

    try:
        # Sample the classification
        sampled = (fsi_class.sample(region=point, scale=500, numPixels=1, geometries=True)
                   .first())

        # FIX: Check if sampled is valid (Handles NoneType error)
        if sampled is None:
            print(f"Clicked ({lat:.4f}, {lon:.4f}): Masked/No Data.")
            return

        result = sampled.getInfo()

        # Double check properties exist
        if result is None or 'properties' not in result:
             print("No properties returned.")
             return

        # Get class value
        class_val = result['properties'].get('Susceptibility_Class')

        # Define labels
        class_names = {
            1: 'Negligible',
            2: 'Minor',
            3: 'Moderate',
            4: 'Substantial',
            5: 'Critical'
        }

        # Print Output
        label = class_names.get(int(class_val), "Unknown") if class_val is not None else "No Data"

        

        return {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "Flood_Susceptibility_Class": f"{class_val}",
            "Description": label
        }

    except Exception as e:
        
        # print(f"Error: {e}")
        pass