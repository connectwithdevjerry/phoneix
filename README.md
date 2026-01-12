# 🌍 LandAlert Solution

**LandAlert** is a Climate Risk and Land Tenure Assessment tool delivered through **Telegram**, designed to provide early warnings and land-related insights using satellite data and geospatial analytics.

Originally developed for **Nigeria**, LandAlert is built on **Google Earth Engine (GEE)** and supports **global datasets**, making it inherently scalable to any country with available satellite coverage.

🔗 **Project Website:** https://landalert-lp.vercel.app/

---

## 📌 Problem Statement

Many communities—especially informal settlements and smallholder farming regions—lack:
- Timely climate risk alerts (flooding, drought, heat stress)
- Accessible land tenure documentation
- Integrated tools linking climate data with land administration systems

This gap increases vulnerability to climate shocks, land disputes, food insecurity, and poor governance outcomes.

---

## 💡 Solution Overview

LandAlert bridges climate intelligence and land governance by:
- Delivering **real-time climate risk alerts via Telegram**
- Leveraging **satellite data and indices** to assess environmental threats
- Linking climate risk information with **land tenure records** through STDM/QGIS
- Supporting **evidence-based decision-making** for governments, NGOs, and communities

---

## 🚀 Key Features

- 🌦 **Climate Risk Monitoring**
  - Flooding risk
  - Drought severity
  - Urban heat stress

- 📡 **Satellite-Powered Analytics**
  - LANDSAT
  - MODIS
  - CHIRPS
  - ERA5
  - GloFAS

- 💬 **Telegram-Based Alert System**
  - Automated alerts
  - Location-aware notifications
  - Open API & webhook support

- 🗺 **Land Tenure & Administration Integration**
  - STDM (Social Tenure Domain Model)
  - QGIS-based land parcel linking
  - Informal land documentation

- 🌱 **Food Security Indicators**
  - NDVI (Normalized Difference Vegetation Index)
  - VCI (Vegetation Condition Index)
  - TCI (Temperature Condition Index)
  - VHI (Vegetation Health Index)

---

## 🏗 System Architecture & Workflow

1. **User Location Input**
   - Users interact with LandAlert via Telegram
   - Location data (coordinates) is captured

2. **Satellite Data Processing**
   - GEE processes climate and environmental datasets
   - Risk indices are computed for the Area of Interest (AOI)

3. **Risk Analysis & Alerting**
   - Flood, drought, and heat risk thresholds are evaluated
   - Alerts are generated and sent via Telegram

4. **Land Record Linking**
   - User and land data are stored using STDM DDL models
   - Climate risks are associated with land parcels and communities

5. **Dashboard & Reporting**
   - Aggregated data is visualized for planning and governance use

---

## 🌍 Global Scalability

LandAlert is **not limited to Nigeria**.

### Supported Global Datasets
- LANDSAT
- MODIS
- CHIRPS
- ERA5
- GloFAS

### How Scaling Works
- Changing the **Area of Interest (AOI)** in GEE enables deployment in any country
- The risk computation pipeline is modular and reusable globally

### Current Limitation
- Free GEE accounts may **time out on large-scale global processing**

🧪 **Global Prototype (GEE):**  
https://code.earthengine.google.com/257e4b33bfc1a5d133720a50d33e4515

### Future Plan
- With a **paid GEE account**, full global deployment becomes feasible
- Meanwhile, **national-level deployment for Nigeria is fully functional**

---

## 💬 Why Telegram (Not WhatsApp)

### Challenge
- WhatsApp APIs have strict limitations for automation and geospatial workflows

### Solution
- Migrated to **Telegram**, which offers:
  - Open APIs & webhooks
  - Native support for geolocation and maps
  - Easier automation
  - Strong global adoption

Telegram provides a more reliable and scalable messaging backbone for LandAlert.

---

## 🗂 STDM / QGIS Integration

LandAlert integrates directly with **STDM (Social Tenure Domain Model)** using QGIS.

### Capabilities
- Store:
  - User name
  - Land use
  - Coordinates
  - Phone number
- Link alerts and field reports to:
  - Land parcels
  - Community land records

### Benefits
- Mapping informal lands and occupancy rights
- Linking households to land parcels
- Storing non-formal tenure evidence
- Supporting land administration workflows

---

## 🌾 Food Security Support

LandAlert strengthens food security monitoring by:
- Tracking vegetation health and crop stress
- Providing early drought warnings
- Supporting farmers, NGOs, and agencies with actionable insights

This enables proactive responses to climate-driven agricultural risks.

---

## 🏛 Land Governance & Administration Vision

### Long-Term Vision
- Enable users to:
  - Verify land registration status
  - Access ownership records
  - Support transparent land governance

### Current Approach
- While official cadastral data requires government collaboration,
  - High-risk informal settlements can be documented
  - Climate-exposed communities can be prioritized for upgrading and intervention

---

## ⚠ Challenges & Limitations

- GEE free-tier computation limits
- Dependency on availability of official cadastral data
- Internet and smartphone access constraints in rural areas

---

## 🔮 Future Improvements

- Paid GEE deployment for full global coverage
- Integration with national cadastral systems
- Web dashboard for policymakers
- SMS fallback for non-smartphone users
- AI-assisted risk interpretation and recommendations

---

## 👤 Author

**Adedeji Jeremiah (Jerry)**  
Geospatial & Web Developer  
Surveying and Geoinformatics  

🔗 GitHub: https://github.com/connectwithdevjerry  
🔗 Website: https://landalert-lp.vercel.app/

---

## 📄 License

This project is open for research, development, and collaboration.  
Licensing terms can be defined based on deployment and partnership needs.
