
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. READ DESNZ SOLAR PV DATA
# ============================================================

file = "ET_6.3_SOLAR_PV_JUL_26.xlsx"
sheet = "Table_1_by_Capacity"

raw = pd.read_excel(
    file,
    sheet_name=sheet,
    header=None
)

dates = raw.iloc[4, 1:]

# Excel row 30 = pandas iloc[29]
# UK TOTAL cumulative installed PV capacity (MW)
cumulative_capacity = raw.iloc[29, 1:]


pv_data = pd.DataFrame({
    "Date": dates,
    "Cumulative Capacity MW": cumulative_capacity
})


pv_data = pv_data.dropna(
    subset=[
        "Date",
        "Cumulative Capacity MW"
    ]
).copy()


pv_data["Cumulative Capacity MW"] = pd.to_numeric(
    pv_data["Cumulative Capacity MW"],
    errors="coerce"
)


# ============================================================
# 2. CLEAN DATES
# ============================================================

pv_data["Date"] = (
    pv_data["Date"]
    .astype(str)
    .str.replace("\n", " ", regex=False)
    .str.strip()
)

pv_data["Date"] = pd.to_datetime(
    pv_data["Date"],
    format="%b %Y"
)

pv_data["Year"] = pv_data["Date"].dt.year


# ============================================================
# 3. MONTHLY NEW DEPLOYMENT
# ============================================================

pv_data["New Capacity MW"] = (
    pv_data["Cumulative Capacity MW"]
    .diff()
)

pv_data.loc[
    pv_data.index[0],
    "New Capacity MW"
] = 0


# Negative differences generally represent
# statistical revisions rather than negative installations
pv_data["New Capacity MW"] = (
    pv_data["New Capacity MW"]
    .clip(lower=0)
)


# ============================================================
# 4. ANNUAL DEPLOYMENT
# ============================================================

annual_deployment = (
    pv_data
    .groupby(
        "Year",
        as_index=False
    )["New Capacity MW"]
    .sum()
)


# ============================================================
# 5. ANNUALISE PARTIAL LATEST YEAR
# ============================================================

latest_year = int(
    pv_data["Year"].max()
)


months_available = (
    pv_data.loc[
        pv_data["Year"] == latest_year,
        "Date"
    ]
    .dt.month
    .nunique()
)


partial_MW = annual_deployment.loc[
    annual_deployment["Year"] == latest_year,
    "New Capacity MW"
].iloc[0]


annualised_MW = (
    partial_MW
    * 12
    / months_available
)


annual_deployment.loc[
    annual_deployment["Year"] == latest_year,
    "New Capacity MW"
] = annualised_MW


print(
    "\nLatest year:",
    latest_year
)

print(
    "Months available:",
    months_available
)

print(
    "Annualised deployment:",
    round(annualised_MW, 1),
    "MW"
)


# ============================================================
# 6. HISTORICAL MODULE EFFICIENCY
# ============================================================

efficiency_data = {
    2010: 0.147,
    2011: 0.152,
    2012: 0.154,
    2013: 0.160,
    2014: 0.163,
    2015: 0.170,
    2016: 0.175,
    2017: 0.177,
    2018: 0.184,
    2019: 0.192,
    2020: 0.200,
    2021: 0.209,
    2022: 0.215,
    2023: 0.220,
    2024: 0.227,
    2025: 0.230,
    2026: 0.232
}


# ============================================================
# 7. MODULE MASS INTENSITY
# ============================================================

# Assumed module mass intensity
MODULE_MASS_KG_M2 = 14.0


def tonnes_per_MW(efficiency):

    # Module output per m² at STC:
    # efficiency × 1000 W/m²

    area_per_MW = (
        1_000_000
        /
        (
            efficiency
            * 1000
        )
    )

    mass_kg = (
        area_per_MW
        * MODULE_MASS_KG_M2
    )

    return (
        mass_kg
        / 1000
    )


annual_deployment[
    "Module Efficiency"
] = (
    annual_deployment["Year"]
    .map(efficiency_data)
)


annual_deployment[
    "Tonnes per MW"
] = (
    annual_deployment[
        "Module Efficiency"
    ]
    .apply(tonnes_per_MW)
)


annual_deployment[
    "PV Installed Tonnes"
] = (
    annual_deployment[
        "New Capacity MW"
    ]
    *
    annual_deployment[
        "Tonnes per MW"
    ]
)


# ============================================================
# 8. ADD PRE-2010 STOCK
# ============================================================

pre_2009_capacity_MW = 14.6
pre_2009_efficiency = 0.135


pre_2009_tonnes_per_MW = tonnes_per_MW(
    pre_2009_efficiency
)


pre_2009_mass = (
    pre_2009_capacity_MW
    *
    pre_2009_tonnes_per_MW
)


pre_2009_cohort = pd.DataFrame({
    "Year": [2008],
    "New Capacity MW": [pre_2009_capacity_MW],
    "Module Efficiency": [pre_2009_efficiency],
    "Tonnes per MW": [pre_2009_tonnes_per_MW],
    "PV Installed Tonnes": [pre_2009_mass]
})


historical_cohorts = pd.concat(
    [
        pre_2009_cohort,
        annual_deployment
    ],
    ignore_index=True
)


# ============================================================
# 9. FUTURE DEPLOYMENT
# ============================================================

FORECAST_END_YEAR = 2055


latest_capacity_MW = float(
    pv_data[
        "Cumulative Capacity MW"
    ].iloc[-1]
)


future_targets = {
    latest_year: latest_capacity_MW,
    2030: 46000,
    2035: 75000,
    2040: 90000,
    2050: 120000,
    2055: 135000
}


target_years = np.array(
    list(
        future_targets.keys()
    )
)


target_capacity = np.array(
    list(
        future_targets.values()
    )
)


future_years = np.arange(
    latest_year,
    FORECAST_END_YEAR + 1
)


future_cumulative = np.interp(
    future_years,
    target_years,
    target_capacity
)


future_df = pd.DataFrame({
    "Year": future_years,
    "Cumulative Capacity MW":
        future_cumulative
})


future_df[
    "New Capacity MW"
] = (
    future_df[
        "Cumulative Capacity MW"
    ]
    .diff()
)


future_df.loc[
    future_df.index[0],
    "New Capacity MW"
] = 0


# Future efficiency pathway
future_df[
    "Module Efficiency"
] = np.interp(
    future_df["Year"],
    [
        2026,
        2030,
        2035,
        2040,
        2050,
        2055
    ],
    [
        0.232,
        0.240,
        0.250,
        0.260,
        0.275,
        0.280
    ]
)


future_df[
    "Tonnes per MW"
] = (
    future_df[
        "Module Efficiency"
    ]
    .apply(tonnes_per_MW)
)


future_df[
    "PV Installed Tonnes"
] = (
    future_df[
        "New Capacity MW"
    ]
    *
    future_df[
        "Tonnes per MW"
    ]
)


future_cohorts = future_df[
    future_df["Year"] > latest_year
][
    [
        "Year",
        "New Capacity MW",
        "Module Efficiency",
        "Tonnes per MW",
        "PV Installed Tonnes"
    ]
].copy()


cohorts = pd.concat(
    [
        historical_cohorts,
        future_cohorts
    ],
    ignore_index=True
)


# ============================================================
# 10. LOW / BASE / HIGH WASTE SCENARIOS
# ============================================================

SCENARIOS = {

    "Low": {
        "mean_lifetime": 35.0,
        "weibull_shape": 5.3759,
        "early_replacement_total": 0.02
    },

    "Base": {
        "mean_lifetime": 30.0,
        "weibull_shape": 5.3759,
        "early_replacement_total": 0.05
    },

    "High": {
        "mean_lifetime": 25.0,
        "weibull_shape": 5.3759,
        "early_replacement_total": 0.10
    }
}


# ============================================================
# 11. EARLY REPLACEMENT DISTRIBUTION
# ============================================================

early_replacement_distribution = {
    12: 0.05,
    13: 0.08,
    14: 0.12,
    15: 0.18,
    16: 0.18,
    17: 0.15,
    18: 0.10,
    19: 0.08,
    20: 0.06
}


# ============================================================
# 12. WEIBULL FUNCTIONS
# ============================================================

def weibull_cdf(
    age,
    mean_lifetime,
    shape
):

    if age <= 0:
        return 0.0

    return (
        1
        -
        np.exp(
            -
            (
                age
                / mean_lifetime
            )
            ** shape
        )
    )


def annual_failure_probability(
    age,
    mean_lifetime,
    shape
):

    if age <= 0:
        return 0.0

    return (
        weibull_cdf(
            age,
            mean_lifetime,
            shape
        )
        -
        weibull_cdf(
            age - 1,
            mean_lifetime,
            shape
        )
    )


def total_failure_probability(
    age,
    mean_lifetime,
    shape,
    early_replacement_total
):

    normal_failure = (
        annual_failure_probability(
            age,
            mean_lifetime,
            shape
        )
    )

    early_replacement = 0.0

    if age in early_replacement_distribution:

        early_replacement = (
            early_replacement_total
            *
            early_replacement_distribution[
                age
            ]
        )

    return (
        normal_failure
        +
        early_replacement
    )


# ============================================================
# 13. ORIGINAL TOTAL WASTE FORECAST
# ============================================================

def calculate_waste_scenario(
    cohorts,
    mean_lifetime,
    shape,
    early_replacement_total
):

    results = []

    for waste_year in range(
        2008,
        FORECAST_END_YEAR + 1
    ):

        annual_waste = 0.0

        for _, cohort in cohorts.iterrows():

            installation_year = int(
                cohort["Year"]
            )

            installed_mass = float(
                cohort[
                    "PV Installed Tonnes"
                ]
            )

            age = (
                waste_year
                -
                installation_year
            )

            if age > 0:

                failure_probability = (
                    total_failure_probability(
                        age,
                        mean_lifetime,
                        shape,
                        early_replacement_total
                    )
                )

                cohort_waste = (
                    installed_mass
                    *
                    failure_probability
                )

                annual_waste += (
                    cohort_waste
                )

        results.append({
            "Year": waste_year,
            "Annual PV Waste Tonnes":
                annual_waste
        })


    scenario_df = pd.DataFrame(
        results
    )


    scenario_df[
        "Cumulative PV Waste Tonnes"
    ] = (
        scenario_df[
            "Annual PV Waste Tonnes"
        ]
        .cumsum()
    )


    return scenario_df


# ============================================================
# 14. CALCULATE TOTAL LOW / BASE / HIGH WASTE
# ============================================================

scenario_results = {}


for scenario_name, settings in SCENARIOS.items():

    scenario_results[
        scenario_name
    ] = calculate_waste_scenario(

        cohorts,

        settings[
            "mean_lifetime"
        ],

        settings[
            "weibull_shape"
        ],

        settings[
            "early_replacement_total"
        ]
    )


waste_low = (
    scenario_results["Low"]
)

waste_base = (
    scenario_results["Base"]
)

waste_high = (
    scenario_results["High"]
)


# ============================================================
# 15. PRINT TOTAL WASTE FORECAST
# ============================================================

print(
    "\nTOTAL PV WASTE FORECAST"
)


for year in [
    2030,
    2040,
    2050
]:

    print(
        "\nYEAR:",
        year
    )

    for scenario_name in [
        "Low",
        "Base",
        "High"
    ]:

        scenario_df = (
            scenario_results[
                scenario_name
            ]
        )

        row = scenario_df.loc[
            scenario_df[
                "Year"
            ] == year
        ].iloc[0]

        print(
            scenario_name,
            "| Annual:",
            f'{row["Annual PV Waste Tonnes"]:,.0f}',
            "tonnes",
            "| Cumulative:",
            f'{row["Cumulative PV Waste Tonnes"]:,.0f}',
            "tonnes"
        )


# ============================================================
# 16. PV ICE FOLDER LOCATIONS
# ============================================================

SOLARGATES_FOLDER = (
    Path(__file__).parent
)


BASELINE_FOLDER = (
    SOLARGATES_FOLDER
    / "PV_ICE-main"
    / "PV_ICE"
    / "baselines"
)


EU_FOLDER = (
    BASELINE_FOLDER
    / "European_baselines_Nagle_2024"
)


print(
    "\nBaseline folder exists:",
    BASELINE_FOLDER.exists()
)

print(
    "EU folder exists:",
    EU_FOLDER.exists()
)


# ============================================================
# 17. PV ICE MATERIAL FILES
# ============================================================

material_files = {

    "Glass":
        EU_FOLDER
        / "baseline_material_mass_glass_EU.csv",

    "Silicon":
        EU_FOLDER
        / "baseline_material_mass_silicon_EU.csv",

    "Copper":
        EU_FOLDER
        / "baseline_material_mass_copper_EU.csv",

    "Silver":
        EU_FOLDER
        / "baseline_material_mass_silver_EU.csv",

    "Aluminium":
        BASELINE_FOLDER
        / "baseline_material_mass_aluminium_frames.csv",

    "Encapsulant":
        BASELINE_FOLDER
        / "baseline_material_mass_encapsulant.csv",

    "Backsheet":
        BASELINE_FOLDER
        / "baseline_material_mass_backsheet.csv"
}


# ============================================================
# 18. READ PV ICE MATERIAL BASELINES
# ============================================================

composition_df = None


for material, filepath in material_files.items():

    print(
        "Reading:",
        filepath.name
    )

    material_df = pd.read_csv(
        filepath,
        skiprows=[1]
    )


    material_df = material_df[
        [
            "year",
            "mat_massperm2"
        ]
    ].copy()


    material_df = (
        material_df.rename(
            columns={
                "year":
                    "Year",

                "mat_massperm2":
                    f"{material} g/m2"
            }
        )
    )


    if composition_df is None:

        composition_df = (
            material_df
        )

    else:

        composition_df = (
            composition_df.merge(
                material_df,
                on="Year",
                how="inner"
            )
        )


# ============================================================
# 19. TOTAL MATERIAL MASS INTENSITY
# ============================================================

materials = [
    "Glass",
    "Silicon",
    "Copper",
    "Silver",
    "Aluminium",
    "Encapsulant",
    "Backsheet"
]


mass_columns = [
    f"{material} g/m2"
    for material in materials
]


composition_df[
    "Total g/m2"
] = (
    composition_df[
        mass_columns
    ]
    .sum(axis=1)
)


# ============================================================
# 20. CONVERT PV ICE DATA INTO MASS FRACTIONS
# ============================================================

for material in materials:

    composition_df[
        f"{material} Fraction"
    ] = (
        composition_df[
            f"{material} g/m2"
        ]
        /
        composition_df[
            "Total g/m2"
        ]
    )


fraction_columns = [
    f"{material} Fraction"
    for material in materials
]


composition_df[
    "Fraction Total"
] = (
    composition_df[
        fraction_columns
    ]
    .sum(axis=1)
)


# ============================================================
# 21. EXTEND 2050 COMPOSITION TO 2055
# ============================================================

# PV ICE composition is effectively held at
# the final available values for these future years.

last_composition = (
    composition_df.loc[
        composition_df["Year"] == 2050
    ]
    .iloc[0]
)


extra_rows = []


for year in range(
    2051,
    FORECAST_END_YEAR + 1
):

    new_row = (
        last_composition.copy()
    )

    new_row["Year"] = year

    extra_rows.append(
        new_row
    )


if extra_rows:

    composition_df = (
        pd.concat(
            [
                composition_df,
                pd.DataFrame(
                    extra_rows
                )
            ],
            ignore_index=True
        )
    )


# ============================================================
# 22. CHECK MATERIAL FRACTIONS
# ============================================================

print(
    "\nPV ICE MATERIAL FRACTIONS"
)


print(
    composition_df[
        [
            "Year"
        ]
        +
        fraction_columns
        +
        [
            "Fraction Total"
        ]
    ]
    .loc[
        composition_df[
            "Year"
        ].isin(
            [
                2000,
                2005,
                2010,
                2015,
                2020,
                2025,
                2030,
                2040,
                2050
            ]
        )
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# 23. MERGE MATERIAL FRACTIONS ONTO INSTALLATION COHORTS
# ============================================================

cohorts = cohorts.merge(
    composition_df[
        [
            "Year"
        ]
        +
        fraction_columns
    ],
    on="Year",
    how="left"
)


# ============================================================
# 24. CHECK FOR MISSING MATERIAL DATA
# ============================================================

missing_material_data = (
    cohorts[
        fraction_columns
    ]
    .isna()
    .any(axis=1)
)


if missing_material_data.any():

    print(
        "\nWARNING:"
        " Some cohorts have missing material composition."
    )

    print(
        cohorts.loc[
            missing_material_data,
            [
                "Year",
                "PV Installed Tonnes"
            ]
        ]
    )


# ============================================================
# 25. MATERIAL-SPECIFIC WASTE
# LOW / BASE / HIGH
# ============================================================

material_scenario_results = {}


for scenario_name, settings in SCENARIOS.items():

    material_waste_results = []


    mean_lifetime = (
        settings[
            "mean_lifetime"
        ]
    )

    shape = (
        settings[
            "weibull_shape"
        ]
    )

    early_replacement_total = (
        settings[
            "early_replacement_total"
        ]
    )


    for forecast_year in range(
        2025,
        FORECAST_END_YEAR + 1
    ):

        total_waste = 0.0


        material_waste = {
            material: 0.0
            for material in materials
        }


        for _, cohort in cohorts.iterrows():

            installation_year = int(
                cohort[
                    "Year"
                ]
            )


            age = (
                forecast_year
                -
                installation_year
            )


            if age <= 0:

                continue


            # --------------------------------------------
            # CORRECT SCENARIO-SPECIFIC FAILURE FUNCTION
            # --------------------------------------------

            p_total = (
                total_failure_probability(
                    age,
                    mean_lifetime,
                    shape,
                    early_replacement_total
                )
            )


            cohort_waste = (
                float(
                    cohort[
                        "PV Installed Tonnes"
                    ]
                )
                *
                p_total
            )


            total_waste += (
                cohort_waste
            )


            # --------------------------------------------
            # SPLIT COHORT WASTE INTO MATERIALS
            # --------------------------------------------

            for material in materials:

                fraction = float(
                    cohort[
                        f"{material} Fraction"
                    ]
                )


                material_waste[
                    material
                ] += (
                    cohort_waste
                    *
                    fraction
                )


        # --------------------------------------------
        # SAVE THIS YEAR
        # --------------------------------------------

        row = {

            "Year":
                forecast_year,

            "Total Waste Tonnes":
                total_waste
        }


        for material in materials:

            row[
                f"{material} Waste Tonnes"
            ] = (
                material_waste[
                    material
                ]
            )


        material_waste_results.append(
            row
        )


    material_scenario_results[
        scenario_name
    ] = pd.DataFrame(
        material_waste_results
    )


# ============================================================
# 26. EASY DATAFRAME NAMES
# ============================================================

material_waste_low = (
    material_scenario_results[
        "Low"
    ]
)


material_waste_base = (
    material_scenario_results[
        "Base"
    ]
)


material_waste_high = (
    material_scenario_results[
        "High"
    ]
)


# ============================================================
# 27. PRINT MATERIAL WASTE FOR 2030 / 2040 / 2050
# ============================================================

for scenario_name in [
    "Low",
    "Base",
    "High"
]:

    print(
        "\n============================================"
    )

    print(
        "MATERIAL COMPOSITION OF PV WASTE -",
        scenario_name.upper()
    )

    print(
        "============================================"
    )


    scenario_df = (
        material_scenario_results[
            scenario_name
        ]
    )


    print(
        scenario_df[
            scenario_df[
                "Year"
            ].isin(
                [
                    2028,
                    2029,
                    2030,
                    2035,
                    2040,
                    2050
                ]
            )
        ].to_string(
            index=False
        )
    )


# ============================================================
# 28. CHECK MATERIAL SUM = TOTAL WASTE
# ============================================================

print(
    "\nMATERIAL MASS BALANCE CHECK"
)


for scenario_name, scenario_df in (
    material_scenario_results.items()
):

    material_sum = (
        scenario_df[
            [
                f"{material} Waste Tonnes"
                for material in materials
            ]
        ]
        .sum(axis=1)
    )


    difference = (
        material_sum
        -
        scenario_df[
            "Total Waste Tonnes"
        ]
    )


    print(
        scenario_name,
        "maximum difference:",
        abs(
            difference
        ).max(),
        "tonnes"
    )


# ============================================================
# 29. EXPORT MATERIAL RESULTS
# ============================================================

material_waste_low.to_csv(
    "PV_material_waste_LOW.csv",
    index=False
)


material_waste_base.to_csv(
    "PV_material_waste_BASE.csv",
    index=False
)


material_waste_high.to_csv(
    "PV_material_waste_HIGH.csv",
    index=False
)


print(
    "\nMaterial waste files exported successfully."
)
for year in [2028, 2029, 2030, 2035, 2040, 2050]:

    print("\n", year)

    for scenario in ["Low", "Base", "High"]:

        df = material_scenario_results[scenario]

        value = df.loc[
            df["Year"] == year,
            "Total Waste Tonnes"
        ].iloc[0]

        print(
            scenario,
            f"{value:,.0f} tonnes"
        )
# ============================================================
# SG C-Si MATERIAL THROUGHPUT
# ============================================================

# Assumed proportion of UK PV waste that is c-Si
C_SI_SHARE = 0.95


# SG market share increases from 8% in 2028
# to 30% in 2050
def sg_market_share(year):

    if year < 2028:
        return 0.0

    return min(
        0.08 + 0.01 * (year - 2028),
        0.30
    )


# ============================================================
# CALCULATE SG MATERIAL THROUGHPUT
# ============================================================

sg_material_results = {}


for scenario_name, df in material_scenario_results.items():

    sg_df = df.copy()


    # --------------------------------------------------------
    # SG MARKET SHARE
    # --------------------------------------------------------

    sg_df["SG Market Share"] = (
        sg_df["Year"]
        .apply(sg_market_share)
    )


    # --------------------------------------------------------
    # c-Si WASTE ONLY
    # --------------------------------------------------------

    sg_df["c-Si Waste Tonnes"] = (
        sg_df["Total Waste Tonnes"]
        * C_SI_SHARE
    )


    # --------------------------------------------------------
    # TOTAL c-Si THROUGHPUT ENTERING SG
    # --------------------------------------------------------

    sg_df["SG c-Si Throughput Tonnes"] = (
        sg_df["c-Si Waste Tonnes"]
        * sg_df["SG Market Share"]
    )


    # --------------------------------------------------------
    # EACH MATERIAL ENTERING SG
    # --------------------------------------------------------

    for material in materials:

        sg_df[
            f"SG {material} Tonnes"
        ] = (
            sg_df[
                f"{material} Waste Tonnes"
            ]
            * C_SI_SHARE
            * sg_df["SG Market Share"]
        )


    sg_material_results[
        scenario_name
    ] = sg_df


# ============================================================
# PRINT YEARS USED IN DISSERTATION
# ============================================================

display_years = [
    2028,
    2029,
    2030,
    2035,
    2040,
    2050
]


for scenario_name in [
    "Low",
    "Base",
    "High"
]:

    print(
        "\n============================================"
    )

    print(
        "SG c-Si MATERIAL THROUGHPUT -",
        scenario_name.upper()
    )

    print(
        "============================================"
    )


    df = sg_material_results[
        scenario_name
    ]


    columns = [
        "Year",
        "SG Market Share",
        "SG c-Si Throughput Tonnes"
    ] + [
        f"SG {material} Tonnes"
        for material in materials
    ]


    print(
        df.loc[
            df["Year"].isin(display_years),
            columns
        ].to_string(
            index=False
        )
    )
    # ============================================================
# 30. PLOT ANNUAL AND CUMULATIVE PV WASTE
# ============================================================

plot_start, plot_end = 2010, FORECAST_END_YEAR
colours = {"Low": "tab:green", "Base": "tab:blue", "High": "tab:red"}


def plot_waste(column, ylabel, title, filename):

    fig, ax = plt.subplots(figsize=(9, 5))

    for name in ["Low", "Base", "High"]:
        df = scenario_results[name]
        df = df[(df["Year"] >= plot_start) & (df["Year"] <= plot_end)]
        ax.plot(
            df["Year"],
            df[column] / 1000,          # tonnes -> kilotonnes
            label=name,
            color=colours[name],
            linewidth=2
        )

    # Shade the range between Low and High
    low = scenario_results["Low"]
    high = scenario_results["High"]
    mask = (low["Year"] >= plot_start) & (low["Year"] <= plot_end)
    ax.fill_between(
        low.loc[mask, "Year"],
        low.loc[mask, column] / 1000,
        high.loc[mask, column] / 1000,
        color="grey",
        alpha=0.15
    )

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xlim(plot_start, plot_end)
    ax.legend(title="Scenario")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(filename, dpi=300)
    plt.show()


plot_waste(
    "Annual PV Waste Tonnes",
    "Annual PV waste (kt)",
    "UK annual end-of-life PV waste forecast",
    "PV_annual_waste.png"
)

plot_waste(
    "Cumulative PV Waste Tonnes",
    "Cumulative PV waste (kt)",
    "UK cumulative end-of-life PV waste forecast",
    "PV_cumulative_waste.png"
)
