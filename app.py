from pathlib import Path 
import pandas as pd
from zipfile import ZipFile
import streamlit as st
import urllib.response
import altair as alt
from sklearn.feature_selection import r_regression
import numpy as np

def line_break():
    st.text("\n")
    st.text("\n")
    st.text("\n")
    st.text("\n")
    st.text("\n")
    st.text("\n")
    st.text("\n")

    return 

def year_range(start_year:int, end_year_exclusive:int):
    return [*range(start_year, end_year_exclusive)]

st.set_page_config(layout="wide")

st.sidebar.title("Sobre")
st.sidebar.info(
    """

    **Visualização Computacional** - SCC0252 

    **Autor**: Heitor Carvalho Pinheiro\n
    **Docente**: Maria Cristina Ferreira de Oliveira

    """
)

st.sidebar.title("Contato") 
st.sidebar.info(
    """
    E-mail: heitor.c.pinheiro@usp.br 
    [LinkedIn](https://www.linkedin.com/in/heitor-carvalho-pinheiro-4b58851b7/) | [Github](https://github.com/Heitorcp) 
    """
)

st.write("# Emissões Globais de CO2 :factory:")

#filtering the years
start_year, end_year = st.select_slider(
    ":date: **Selecione os anos que deseja observar**",
    options = [*range(1750, 2023)], value = (1900, 2022))

def pivot_df(df, index:str, columns:str, values:str):
    
    pivot_df = pd.pivot(df, index=index, columns=columns, values=values)
    return pivot_df

@st.cache
def read_CO2_data():
    try:
        csv_path = Path("data/GCB2022v27_MtCO2_flat.csv")
    except:
        if not csv_path.is_file():
            Path("data").mkdir(parents=True, exist_ok=True)
            with ZipFile("data/archive.zip", 'r') as zObject:
                zObject.extractall(path="data")
    return pd.read_csv(Path("data/GCB2022v27_MtCO2_flat.csv"))

@st.cache 
def data_with_coords():
    try:
        data = read_CO2_data().iloc[:, [0] + [*range(2,11)]] 
        coords = pd.read_csv("./data/country-coord.csv", usecols=[0,3,4,5], dtype={'Numeric code':str})
        coords = coords.rename(columns={"Numeric code":"id"})

        df_with_coords = data.join(coords.set_index('Country'), on='Country')
        #filter years 
        df_with_coords = df_with_coords.set_index('Year').loc[year_range(2000,2022)].reset_index()

    except BaseException as e:
        raise e

    return df_with_coords


def data_with_coords_r2_score():
    try:
        years = [*range(2000,2022)]
        data = data_with_coords().iloc[:,[0,1,2,10,11,12]]
        data = data.set_index("Year").loc[years].reset_index()
        data_groupped = data.groupby("Country")

        r2_dict = {}

        countries = data.Country.unique() 

        for country in countries:

            df = data_groupped.get_group(country) 

            X = df.iloc[:, [0]]
            y = df.iloc[:, 2]
            r2_score = r_regression(X,y)[0]
            r2_score = r2_score.round(2)

            r2_dict[country] = r2_score 

        df_final = pd.DataFrame.from_dict(r2_dict, orient="index", columns=["r2_score"]).reset_index()
        df_final.columns = ["Country", "r2_score"]

        conditions = [

        df_final['r2_score'] < -0.8,
        (df_final['r2_score'] < -0.6) & (df_final['r2_score'] >= -0.8),
        (df_final['r2_score'] <= 0.6) & (df_final['r2_score'] >= 0.),
        (df_final['r2_score'] <= 0.)  & (df_final['r2_score'] >= -0.6),
        (df_final['r2_score'] <= 0.8) & (df_final['r2_score'] >= 0.6),
        df_final['r2_score'] > 0.8

                    ]

        choices = ["Group A", "Group B", "Group C", "Group C", "Group D", "Group E"]

        df_final["Group"] = np.select(conditions, choices)

        #merging coords with groups
        data = data.iloc[:, [1,3,4,5]]

        df_groups = pd.merge(data, df_final, on="Country")
        df_groups.drop_duplicates(inplace=True)

    except BaseException as e:
        raise e

    return df_groups

print(data_with_coords_r2_score())

def emission_per_category():
    
    df_per_category = read_CO2_data()[read_CO2_data().Country != "Global"]
    df_per_category = df_per_category.groupby(["Year","Coal","Oil","Gas","Cement","Flaring","Other"]).sum()
    df_per_category = df_per_category.reset_index()
    df_per_category = df_per_category.iloc[:,[0,1,2,3,4,5,6]]
    df_per_category = df_per_category.set_index("Year").loc[years]
    df_per_category = df_per_category.reset_index().melt(id_vars=["Year"], var_name = "Category", value_name="Total")
    df_per_category = df_per_category.astype({"Year":"string","Category":"string", "Total":"float64"})
    df_per_category = df_per_category.groupby(["Year","Category"])["Total"].sum().reset_index()
    
    return df_per_category

@st.cache
def rank_by_column(column_to_rank_by:str = ["Total", "Oil", "Coal", "Gas", "Flaring", "Cement", "Other", "Per Capita"]) -> pd.DataFrame():

    years = year_range(2000, 2022)

    df = read_CO2_data().loc[(read_CO2_data().Year.isin(years)) & (read_CO2_data().Country != "Global")]
    column_ranked = df[[column_to_rank_by, "Year", "Country"]].sort_values(by=["Year",column_to_rank_by], ascending=(True, False))
    
    ranks = column_ranked.groupby("Year")[column_to_rank_by].rank(method='first', ascending=False).reset_index()
    ranks.rename(columns={column_to_rank_by:"Rank"}, inplace=True)

    #joining on index 
    ranked_df = column_ranked.join(ranks.set_index('index'), on=column_ranked.index)  
    return ranked_df

try:
    df_raw = read_CO2_data()
    df = df_raw.iloc[:,[0,2,3]]
    df = df[df.Year.isin(range(start_year, end_year))]
    # print(df)

    countries = st.multiselect(
        ":earth_americas: **Selecione os países**", list(df.Country.unique()), ["USA", "China", "Russia",
        "Germany", "United Kingdom", "Japan", "India", "France","Canada"]
    ) 
    if not countries:
        st.error("Please select at least one country.")
    else:

        #df-wide format
        df = pivot_df(df, index='Country', columns='Year', values='Total')
        df = df.loc[countries]

        # st.write("Annually CO2 Emission", df.sort_index())

        #df long-format
        df =df.T.reset_index()
        df = df.astype({"Year":"str"})
        df = pd.melt(df, id_vars=["Year"]).rename(columns={
            "value":"Total (kt)"
        })

        area_chart = (
            alt.Chart(df).mark_area(opacity=0.4).encode(
                x="Year:T",
                y=alt.Y("Total (kt):Q", stack=None),
                color="Country:N"
            )
        )

        st.altair_chart(area_chart, use_container_width=True)
except urllib.error.URLError as e:
    st.error(
        """
        **This dashboard requires internet access.**
        Conection error: %s
        """
        % e.reason
    )

st.markdown("O gráfico acima, por *default*, representa os 9 países com as maiores emissões de CO2, por kilotoneladas, ao longo dos últimos 120 anos.\n\
    Fica evidente a tendência de crescimento da emissão ao longo dos anos.")

#LAYING OUT THE MIDDLE SECTION OF THE APP 
row2_1, row_2_2 = st.columns((2,1))

with row2_1:
    st.subheader("Maiores emissores de CO2")
    st.write("**With the highest historical CO2 emissions**")

    try:
        total_by_country = df_raw.groupby('Country')['Total'].sum().reset_index() 

        top_10_countries = total_by_country.sort_values(by="Total", ascending=False)[1:11]
        top_10_countries = top_10_countries.astype({"Total":"float64", "Country":"string"})

        bar_chart_top10 = alt.Chart(top_10_countries).mark_bar().encode(
                x=alt.X('Total:Q'),
                y = alt.Y('Country:N', sort="-x"),
                color=alt.Color(
                    "Country",
                    scale=alt.Scale(
                    domain = top_10_countries.Country.tolist(),
                    range = ['red']*3+['steelblue']*7),
                    legend=None
                )
            )

        st.altair_chart(bar_chart_top10, use_container_width=True)

    except BaseException as e:
        raise e

with row_2_2:
    line_break()
    st.markdown("Os três maiores países com as maiores taxas de emissões de CO2 históricas são os :red[países mais populosos]")

row_3_1, row_3_2 = st.columns((3,1))

with row_3_1:
    st.subheader("Menores emissores de CO2")
    st.write("**With the lowest historical CO2 emissions**")

    try:
        total_by_country = df_raw.groupby('Country')['Total'].sum().reset_index() 

        top_10_low_countries = total_by_country.sort_values(by="Total", ascending=True)[:10]
        top_10_low_countries = top_10_low_countries.astype({"Total":"float64", "Country":"string"})

        bar_chart_top10_low = alt.Chart(top_10_low_countries).mark_bar().encode(
                x=alt.X('Total:Q'),
                y = alt.Y('Country:N', sort="x"),
                color=alt.Color(
                    "Country",
                    scale=alt.Scale(
                    domain = top_10_low_countries.Country.tolist(),
                    range = ['green']*3+['steelblue']*7),
                    legend=None
                )
            )

        st.altair_chart(bar_chart_top10_low, use_container_width=True)

    except BaseException as e:
        raise e

with row_3_2:
    line_break()
    st.markdown("Os três países com as menores taxas de emissões de CO2 históricas são os :green[países que apresentam as menores taxas populacionais]")

st.markdown("## Variação Anual para o período de 2000-2020")
st.markdown("### Emissão Total por ano")
st.markdown("Como observado no início, nos últimos 20 anos a tendência observada é de crescimento an emissão de CO2.\n \
    As quedas observadas em 2008 e 2019, referem-se, respectivamente, à crise imobiliária de 2008 e à pandemia do COVID-19")

years = year_range(2000, 2022)

try:
    df_last_22_years = df_raw[df_raw.Country != "Global"].groupby("Year")["Total"].sum().reset_index() 
    df_last_22_years = df_last_22_years.set_index("Year")
    df_last_22_years = df_last_22_years.loc[years].reset_index()
    df_last_22_years = df_last_22_years.astype({"Year":"string", "Total":"float64"})

    annual_change_total_chart = alt.Chart(df_last_22_years).mark_line(point=True).encode(
        x=alt.X("Year:T", timeUnit="year", title="Year"),
        y="Total:Q"
    )

    st.altair_chart(annual_change_total_chart, use_container_width=True)

except BaseException as e:
    raise e

st.markdown("### Emissão total por ano por categoria")
st.markdown("A emissão de **carvão** (Coal), **gás** (Gas) e **óleo** (Oil), as três maiores fontes de emissão, diminuíram durante os anos de 2008 (crise financeira mundial) e 2019 (Covid-19) \
    Apesar disso, a tendência continua de crescimento nos últimos anos")

try:
    
    annual_emission_per_category = alt.Chart(emission_per_category()).mark_line(point=True).encode(
        x=alt.X("Year:T", timeUnit="year", title="Year"),
        y="Total:Q",
        color="Category"
    )

    st.altair_chart(annual_emission_per_category, use_container_width=True)

except BaseException as e:
    raise e

row_4_1, row_4_2 = st.columns([2.5,1])

with row_4_2:
    try:

        line_break()
        st.text("\n")
        st.text("\n")
        st.text("\n")
        
        emission_source = st.selectbox(
            ':pick: **Selecione uma fonte de emissão**',
            ("Total", "Coal", "Oil", "Gas", "Cement", "Flaring", "Other", "Per Capita")
        )

        st.write("Você selecionou:", emission_source)

        df_ranked = rank_by_column(column_to_rank_by=emission_source)
        df_ranked = df_ranked[~df_ranked.loc[:,emission_source].isnull()]
        df_ranked = df_ranked.astype({"Rank":"int64", emission_source:"float64", "Year":"string", "Country":"string"})

        countries_rank = st.multiselect(
        ":earth_americas: **Selecione os países**", list(read_CO2_data().Country.unique()), ["USA", "China", "Russia",
        "Germany", "United Kingdom", "Japan"])

        df_ranked = df_ranked[df_ranked.Country.isin(countries_rank)].sort_values(by=["Year", "Rank"], ascending=(True, False))

        if not countries_rank:
            st.error("Selecione um país, pelo menos.")

    except BaseException as e:
        raise e

with row_4_1:
    try:
        st.markdown("# Ranking de países")
        st.markdown("Selecione a **fonte de emissão** e o **país** no filtro ao lado para verificar o rank dos países durante os anos de 2000-2020.\n\
              \n**Emissões per capita** pode corrigir sua visão sobre o número de emissões por país.\n \
                Por exemplo, China lidera o número de emissões total há 15 anos, porém, em emissões per capita USA é o líder.")

        countries_rank_chart = alt.Chart(df_ranked).mark_line(point=True).encode(
            x=alt.X("Year:T", timeUnit="year", title="Year"),
            y=alt.Y("Rank:Q",
                    sort="descending",
                    scale=alt.Scale(domain=[1,df_ranked.Rank.max()]),
                    axis=alt.Axis(values=[i for i in range(1,df_ranked.Rank.max())], tickMinStep=1)),
            color="Country"
        ).properties(
                        title="Ranking dos países",
                        width=800,
                        height=400
                    )

        st.altair_chart(countries_rank_chart, use_container_width=True)

    except BaseException as e:
        raise e

    
st.markdown("# Grupos de Países")
st.markdown("Os 231 países foram divididos em 5 grupos de acordo com o coeficiente de determinação $R^{2}$ resultante do ajuste de um modelo \
    de Regressão Linear entre os anos e o total de emissões.")
st.markdown("Selecione ao lado o **Grupo de países** que deseja observar.")

row_5_1, row_5_2 = st.columns([4,1])

with row_5_2:

    group_box = st.selectbox(
    ':factory: **Grupo**',
    ("All groups", "Group A", "Group B", "Group C", "Group D", "Group E")
    ) 

    if group_box == "All groups":
        lookup_data = data_with_coords_r2_score()
    else:
        lookup_data = data_with_coords_r2_score().set_index("Group").loc[group_box].reset_index()

    st.markdown("#### Grupo A")
    st.markdown("Esse grupo apresentou uma tendência clara de redução de emissões ao longo dos anos de 2000-2021")
    st.markdown("#### Grupo B")
    st.markdown("Esse grupo apresentou uma tendência não muito expressiva de redução de emissões ao longo dos anos de 2000-2021")
    st.markdown("#### Grupo C")
    st.markdown("Esse grupo não apresentou uma tendência clara de redução ou aumento de emissões ao longo dos anos de 2000-2021")
    st.markdown("#### Grupo D")
    st.markdown("Esse grupo apresentou uma tendência de aumento não muito expressiva de emissões ao longo dos anos de 2000-2021")
    st.markdown("#### Grupo E")
    st.markdown("Esse grupo apresentou uma tendência clara de aumento de emissões ao longo dos anos de 2000-2021")

with row_5_1:

    from vega_datasets import data

    countries = alt.topo_feature(data.world_110m.url, "countries")

    background = alt.Chart(countries).mark_geoshape(fill='white')

    foreground = alt.Chart(countries).mark_geoshape(
        stroke='black'
    ).encode(
        color=alt.Color(
            "Group:O", scale=alt.Scale(scheme="lightgreyred"), legend=None,
        ),
        tooltip=[
            alt.Tooltip("Country:N", title="Country"),
            alt.Tooltip("r2_score:Q", title="R2 Score"),
            alt.Tooltip("Group:O", title="Group"),
        ],
    ).transform_lookup(
        lookup="id",
        from_=alt.LookupData(lookup_data, "id", ["Group", "Country", "r2_score"])
    )

    final_map = (
    (background + foreground)
    .configure_view(strokeWidth=0)
    .properties(width=1200, height=800)
    .project("naturalEarth1")

    )

    st.altair_chart(final_map, use_container_width=True)

