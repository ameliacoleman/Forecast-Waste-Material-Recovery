# Forecast-Waste-Material-Recovery
This script reads UK solar PV capacity data, calculates new installs each year, and converts MW to tonnes using panel efficiency. It projects capacity from 2008 to 2055, then uses a Weibull lifetime model (low/base/high) to forecast when panels become waste. PV ICE data splits that waste into materials, and estimates how much c-Si waste could be recycled. This repository presents forecasts of end-of-life solar photovoltaic (PV) panel waste in the UK from 2008 to 2055. It shows how much PV waste is expected each year and in total, under three scenarios for how long panels last.

Contents
PV_annual_waste.png: forecast annual PV waste (tonnes) under Low, Base and High scenarios
PV_cumulative_waste.png: forecast cumulative PV waste (tonnes) under the same scenarios
How the forecast was made

1. Installed capacity Historical UK solar capacity comes from the Department for Energy Security and Net Zero (DESNZ) solar PV deployment statistics. Monthly cumulative capacity was converted into the amount of new capacity installed each year. Future capacity was projected to reach 46 GW by 2030, 90 GW by 2040, 120 GW by 2050 and 135 GW by 2055.

2. Converting capacity to mass Each year's installed capacity (MW) was converted to tonnes of panels. This used the average module efficiency for that year, which rises from about 15% in 2010 to 23% in 2026 and a projected 28% by 2055, together with an assumed module mass of 14 kg/m². More efficient panels need less area, and therefore less material, per MW.

3. When panels reach end of life Each year's installations were treated as a group, or cohort, that retires gradually over time following a Weibull lifetime distribution. A small share was also assumed to be replaced early, between 12 and 20 years, because of damage, faults or repowering.

Scenario	Mean lifetime	Early replacement
Low	35 years	2%
Base	30 years	5%
High	25 years	10%

Shorter lifetimes and more early replacement mean waste arrives sooner, which is why the High scenario rises fastest.

4. Material breakdown Total waste was split into glass, silicon, copper, silver, aluminium, encapsulant and backsheet, using material composition data from PV ICE (see below). Each cohort's waste was split using the composition of panels made in the year it was installed.

Where the PV ICE data comes from

PV ICE (PV in the Circular Economy) is an open-source tool developed by the National Renewable Energy Laboratory (NREL) in the United States. It models the materials in solar panels and what happens to them at end of life.

PV ICE provides baseline files giving the mass of each material, in grams per square metre of panel, for each manufacturing year. These baselines are compiled from industry roadmaps, manufacturer data and published literature. They track how panel design has changed over time, such as thinner silicon wafers and less silver per cell.

This project used:

European baselines for glass, silicon, copper and silver, from the European_baselines_Nagle_2024 folder (Nagle et al., 2024). These reflect panels installed in Europe, which suits a UK analysis.
Standard PV ICE baselines for aluminium frames, encapsulant and backsheet.

The mass values were converted into material fractions (the share of each material in a panel) and applied to the UK waste forecast. Composition beyond 2050 was held at 2050 values.

PV ICE repository: https://github.com/NREL/PV_ICE

Data sources
DESNZ, Solar photovoltaics deployment statistics (ET 6.3), July 2026 release
NREL, PV ICE: https://github.com/NREL/PV_ICE
Nagle et al. (2024), European material baselines, included in the PV ICE repository
Limitations
Future capacity and efficiency pathways are assumptions, not official forecasts.
A single module mass (14 kg/m²) is used for all years.
Early replacements are added on top of normal lifetime failures, so a small amount of waste may be counted twice over the full period.
