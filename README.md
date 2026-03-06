# 🌍 Open Data Source Analysis & Planning Project

## Project Information

**Project Name:**  
Analisis Pengaruh Stabilitas Politik terhadap Pertumbuhan Ekonomi Dunia Berbasis Data Terbuka dengan Pendekatan Machine Learning  

**Created By:** Data Engineering Team 4  
**Date:** February 20, 2026  
**Version:** 1.0

---

# 📄 Executive Summary

## Project Overview

**Tujuan Project:**  
Mengembangkan sistem analitik berbasis data terbuka untuk menganalisis hubungan antara stabilitas politik dan pertumbuhan ekonomi global serta membangun model Machine Learning untuk memprediksi GDP Growth berdasarkan indikator politik dan ekonomi.

### Scope Project
- Integrasi data politik dan ekonomi global  
- Data cleaning dan harmonisasi panel country-year  

### Expected Outcomes
- Dataset global terintegrasi (2006–2024)  
- Analisis hubungan stabilitas politik dan pertumbuhan ekonomi  
- Model Machine Learning untuk prediksi GDP Growth  

### Timeline
3 bulan (Maret – Mei 2026)

---

# 👥 Stakeholders

**Project Owner:**  
Global Economic Policy Research Initiative  

### Team Members
- **Data Engineer:** Moch. Arrizal Syach P  
- **Data Analyst:** Alivia Rizka Wardani  
- **Project Manager:** Dava Febri Wardana  

### End Users
- Economic Research Institutions  
- Academic Researchers  
- Public Data Community  

---

# 📊 Data Source Analysis

## 1️⃣ Data Politik – Democracy Index

### Source Details

**Dataset Name:**  
Democracy Index (2006–2024)

**URL / Access Point:**  
https://ourworldindata.org/grapher/democracy-index-eiu?tab=table  

**Data Owner:**  
Economist Intelligence Unit  

**Update Frequency:**  
Annual  

### Data Analysis

**Format Data:** JSON  

**Volume Data:**  
±5–10 MB  

**Time Coverage:**  
2006–2024  

### Data Quality

- **Completeness:** 98% (beberapa negara kecil tidak tersedia di awal tahun)  
- **Accuracy:** High (expert-based assessment)  
- **Consistency:** Good (format tahunan konsisten)  
- **Timeliness:** Updated yearly  
- **Standardization:** Sudah dalam format panel data (country-year)  

---

# 2️⃣ Data Ekonomi – World Development Indicators (Inflation)

### Source Details

**Dataset Name:**  
Inflation, Consumer Prices (Annual %)

**URL / Access Point:**  
https://data.worldbank.org/indicator/NY.GDP.DEFL.KD.ZG?most_recent_value_desc=false  

**Data Owner:**  
World Bank  

**Update Frequency:**  
Annual  

### Data Analysis

**Format Data:**  
CSV / Excel  

**Volume Data:**  
±20 MB  

### Data Fields

- country  
- country  
- inflation_rate (%)  

### Quality Metrics

- **Completeness:** 95% (beberapa negara konflik memiliki missing values)  
- **Accuracy:** High (official national statistics)  
- **Consistency:** Very Good (standar internasional)  
- **Timeliness:** Updated annually  
- **Data Type Quality:** Numeric, structured  

---

# 3️⃣ Data Ekonomi – GDP Data

### Source Details

**Dataset Name:**  
GDP Growth (Annual %)

**URL / Access Point:**  
https://data.worldbank.org/indicator/NY.GDP.PCAP.KD.ZG?most_recent_value_desc=false  

**Source:**  
World Bank  

**Access Method:**  
CSV Extract (World Development Indicators)

**Update Frequency:**  
Annual  

### Data Analysis

**Format Data:** CSV  

**Volume Data:**  
±10 MB  

**Time Coverage:**  
1960–2024  

### Data Fields

- country  
- year  
- gdp_growth (%)  

### Data Quality

- **Completeness:** 97%  
- **Accuracy:** High (official macroeconomic reporting)  
- **Consistency:** Good (panel time-series format)  
- **Timeliness:** Annual update  
- **Outliers:** Possible during crisis years (2008, 2020 pandemic)  

---

# 📌 Notes

Dataset yang digunakan dalam project ini berasal dari sumber **open data internasional**, yaitu:

- Our World in Data  
- World Bank – World Development Indicators  

Dataset tersebut digunakan untuk menganalisis hubungan antara **stabilitas politik dan pertumbuhan ekonomi global** serta mendukung pengembangan model **Machine Learning** untuk prediksi GDP Growth.

---
