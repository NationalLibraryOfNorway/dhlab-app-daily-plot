# -*- coding: utf-8 -*-

import streamlit as st
import dhlab.api.dhlab_api as api
import pandas as pd
from PIL import Image, ImageEnhance
import json
import datetime
import matplotlib.pyplot as plt
from io import BytesIO

import altair as alt

from urllib.parse import urlencode

def make_nb_query(name, start_date, end_date):
    return "https://www.nb.no/search?mediatype=aviser&" + urlencode({'q': f"{name}", 'fromDate': f"{start_date.strftime('%Y%m%d')}", 'toDate': f"{end_date.strftime('%Y%m%d')}"})

max_days = 7400
min_days = 3

# @st.cache(suppress_st_warning=True, show_spinner=False)
@st.cache_data()
def to_excel(df):
    """Make an excel object out of a dataframe as an IO-object"""
    output = BytesIO()
    #writer = pd.ExcelWriter(output, engine='openpyxl')
    #df.to_excel(writer, index=True, sheet_name='Sheet1')
    #worksheet = writer.sheets['Sheet1']
    #writer.save()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


#@st.cache(suppress_st_warning=True, show_spinner = False)
@st.cache_data()
def titles():
    b = pd.read_csv('titles.csv')
    return list(b.title)

# @st.cache(suppress_st_warning=True, show_spinner = False)
@st.cache_data()
def sumword(words, period, title = None):
    wordlist =   [x.strip() for x in words.split(',')]
    # check if trailing comma, or comma in succession, if so count comma in
    if '' in wordlist:
        wordlist = [','] + [y for y in wordlist if y != '']
    try:
        ref = api.ngram_news(wordlist, period = period, title = title).sum(axis = 1)
        ref.columns = 'tot'
        ref.index = ref.index.map(pd.Timestamp)
    except AttributeError:
        st.write('...tom ramme for sammenligning ...')
        ref = pd.DataFrame()
    return ref


# @st.cache(suppress_st_warning=True, show_spinner = False)
@st.cache_data()
def ngram(word, mid_date, sammenlign, title = None):
    #st.write('innom')
    period = ((mid_date - datetime.timedelta(days = max_days)).strftime("%Y%m%d"),
              (mid_date + datetime.timedelta(days = max_days)).strftime("%Y%m%d"))
    try:
        res = api.ngram_news(word, period = period, title = title).fillna(0).sort_index()
        res.index = res.index.map(pd.Timestamp)

        if sammenlign != "":
            tot = sumword(sammenlign, period = period, title = title)
            for x in res:
                res[x] = res[x]/tot
    except AttributeError:
        st.write('... tom ramme for ord ...')
        res = pd.DataFrame()
    return res

# @st.cache(suppress_st_warning = True, show_spinner = False)
@st.cache_data()
def adjust(df, date, days, smooth):
    res = df
    
    try:
        ts = pd.Timestamp(date)
        td = pd.Timedelta(days = days - 1)
        s = pd.Timestamp(min(pd.Timestamp("20210701"), pd.Timestamp((ts - pd.Timedelta(days = days + min_days)))).strftime("%Y%m%d"))
        e = pd.Timestamp(min(pd.Timestamp.today(), pd.Timestamp((ts + td))).strftime("%Y%m%d"))
        mask = (df.index >= s) & (df.index <= e)
        
        #st.write(s,e)
        #st.write(df.loc[s])
        
        res = df.loc[mask].rolling(window = smooth).mean()
    
    except AttributeError:
        st.write('...tom ramme...')
    
    return res.fillna(0).applymap(int)

st.set_page_config(page_title="Dagsplott", layout="wide", initial_sidebar_state="auto", menu_items=None)
st.session_state.update(st.session_state)



cola, colb = st.columns([4,1])
with cola:
    st.markdown('## Dagsplott for aviser')

with colb:
    im = Image.open("DHlab_logo_web_en_black.png").convert('RGBA')
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(.4)
    im.putalpha(alpha)
    st.image(im, width = 300)
    st.markdown("""[DH ved Nasjonalbiblioteket](https://nb.no/dh-lab)""")
st.markdown("---")
st.markdown('### Trendlinjer')

################################### Sammenlign ##################################

colw, cols, cola, coldmidt, coldperiode, colg  = st.columns([3,2,2,1,1,1])
with colw:
    words = st.text_input('Enkeltord', "frihet", help="Skriv inn ett eller flere enkeltord adskilt med komma. Det er forskjell på store og små bokstaver")
    allword = list(set([w.strip() for w in words.split(',')]))[:30]

with cols:
    #sammenlign = st.text_input("Relativt til", ". ,", help="Sammenlingn med summen av en liste med ord. Om listen ikke er tom viser y-aksen antall forekomster pr summen av ordene det sammenlignes med. Er listen tom viser y-aksen det absolutte antall forekomster ")
    sammenlign = ""
with cola:
    avisnavn = st.selectbox("Velg avis", titles(), index=0, help="Begynn å skrive navnet på en avis, og velg fra listen, om ingen avis velges aggregreres over alle")
    if avisnavn == "--ingen--":
        avisnavn = None

with colg:
    smooth_slider = st.slider('Glatting', 1, 21, 3)


last_date = datetime.datetime.strptime("20200701", '%Y%m%d')

with coldmidt:
    mid_date = st.date_input('Dato', value=last_date - datetime.timedelta(days = int(max_days/2)),
                            min_value = datetime.date(1763, 5, 1), max_value = datetime.date.today())
with coldperiode:
    period_size = st.number_input(f"Periode", min_value= min_days, max_value = max_days, value = max_days,step=100, help="Lengde på periode i antall dager, maks {max_days}, minimum {min_days}")
    start_date = min(datetime.date.today() - datetime.timedelta(days = 2), mid_date - datetime.timedelta(days = period_size))
    end_date = min(datetime.date.today(), mid_date + datetime.timedelta(days = period_size))

    period = (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))


schemes = ['accent',
 'category10',
 'category20',
 'category20b',
 'category20c',
 'dark2',
 'paired',
 'pastel1',
 'pastel2',
 'set1',
 'set2',
 'set3',
 'tableau10',
 'tableau20',
 'blues',
 'greens',
 'oranges',
 'reds',
 'purples',
 'greys',
 'viridis',
 'magma',
 'inferno',
 'plasma',
 'bluegreen',
 'bluepurple',
 'greenblue',
 'orangered',
 'purplebluegreen',
 'purpleblue',
 'purplered',
 'redpurple',
 'yellowgreenblue',
 'yellowgreen',
 'yelloworangebrown',
 'yelloworangered',
 'blueorange',
 'brownbluegreen',
 'purplegreen',
 'pinkyellowgreen',
 'purpleorange',
 'redblue',
 'redgrey',
 'redyellowblue',
 'redyellowgreen',
 'spectral']

df = ngram(allword, mid_date, sammenlign, title = avisnavn)


df_for_print = adjust(df, mid_date, period_size, smooth_slider).reset_index().rename(columns = {'index':'Dato'})

# konverter til altair long form

df_alt = df_for_print.melt('Dato', var_name='Token', value_name='Frekvens')

## Kode merket med ## er for å legge til tooltip på grafen - fungerer ikke så bra
df_alt['url'] = df_alt['Token'].apply(lambda x:make_nb_query(x, start_date, end_date))

ngram_chart = alt.Chart(df_alt, height=500).mark_line().encode(
    x = alt.X('Dato:T'),
    y = alt.Y('Frekvens:Q'),
    color = alt.Color('Token', scale = alt.Scale(scheme = st.session_state.get('theme', 'tableau20'))),
    href='url',
    tooltip=['Token', 'Dato', 'Frekvens']
).configure_mark(
    opacity = st.session_state.get('alpha', 0.9),
    strokeWidth = st.session_state.get('width',3.0)
)

ngram_chart['usermeta'] = {
    "embedOptions": {
        'loader': {'target': '_blank'}
    }
}

st.altair_chart(ngram_chart, theme=None, use_container_width=True)



#st.line_chart(cars)

# lagre til fil

colf, col2, col_theme, col_alpha, col_width = st.columns([3,3,2,2,2])
with colf:
    filnavn = st.text_input("Last ned data i excelformat", f"dagsplott_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.xlsx", help="Filen blir sannsynligvis liggende i nedlastningsmappen - endre gjerne på filnavnet, men behold .xlsx")

if st.download_button(f'Klikk for å laste ned til {filnavn}', to_excel(df), filnavn, help = "Åpnes i Excel eller tilsvarende"):
    pass

with col_theme:
    theme = st.selectbox("Angi farger", schemes, index=schemes.index('tableau20'), key='theme', help="Palettene er beskrevet her: https://vega.github.io/vega/docs/schemes/#reference")
with col_alpha:
    alpha = st.number_input("Gjennomsiktighet", min_value= 0.1, max_value=1.0, value = st.session_state.get('alpha', 0.9), step=0.1, key='alpha', help="Jo mindre verdi jo mer gjennomsiktig")
with col_width:
    width = st.number_input("Linjetykkelse", min_value = 0.5, max_value=20.0, value = st.session_state.get('width',3.0), step=1.0, key='width', help="Linjene justeres i enheter på 0.5")




