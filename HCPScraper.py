import streamlit as st
import pandas as pd
import subprocess

subprocess.run(["playwright", "install"], check=True)
subprocess.run(["playwright", "install-deps"], check=True)
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Set up Streamlit interface
st.title("Gesgolf Handicap Scraper")
st.write("Please enter your **GesGolf** credentials below:")

# Get user input for NrTessera and Password
nr_tessera = st.text_input("Nr Tessera", "")
password = st.text_input("GesGolf Password", "", type="password")

# Button to start scraping
if st.button("Start Scraping"):
    if not nr_tessera or not password:
        st.error("Please enter both NrTessera and Password")
    else:
        # Initialize an empty DataFrame
        df = pd.DataFrame(columns=["Handicap", "Cognome", "Nome"])

        # URLs for login and data
        loginurl = "https://www.gesgolf.it/SMSPrenotazioni2014/AreaRiservata/Tesserati/Login.aspx"
        secondurl = "https://www.gesgolf.it/SMSPrenotazioni2014/AreaRiservata/Tesserati/ElencoHandicap.aspx"

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True, slow_mo=200)
            page = browser.new_page()
            page.goto(loginurl)

            # Fill the login fields with user input
            page.fill("input#cpCorpo_txtNrTessera", nr_tessera)
            page.fill("input#cpCorpo_txtPassword", password)
            page.click('input[type=submit]')
            
            page.goto(secondurl)

            # Scrape left pages (1-10)
            for i in range(1, 11):
                if i > 1:  # Navigate for pages 2-10
                    page.locator("#cpCorpo_gv_Handicap").get_by_role("cell", name=str(i), exact=True).click()
                    page.wait_for_selector('#cpCorpo_gv_Handicap')
                    
                html2 = page.inner_html('#cpCorpo_gv_Handicap')
                table = BeautifulSoup(html2, "html.parser")
                column_data = table.find_all("tr")

                for row in column_data[1:]:
                    row_data = row.find_all("td")
                    individual_row_data = [data.text.strip() for data in row_data]
                    if len(individual_row_data) == len(df.columns):
                        df.loc[len(df)] = individual_row_data

            st.subheader("First 200 Golfers Scraped ...")

            # Scrape right pages (1-7)
            for i in range(1, 8):
                if i > 1:  # Navigate for pages 2-7
                    page.locator("#cpCorpo_gv_HandicapNZ").get_by_role("cell", name=str(i), exact=True).click()
                    page.wait_for_selector('#cpCorpo_gv_HandicapNZ')
                    
                html3 = page.inner_html('#cpCorpo_gv_HandicapNZ')
                table = BeautifulSoup(html3, "html.parser")
                column_data = table.find_all("tr")

                for row in column_data[1:]:
                    row_data = row.find_all("td")
                    individual_row_data = [data.text.strip() for data in row_data]
                    if len(individual_row_data) == len(df.columns):
                        df.loc[len(df)] = individual_row_data

            # Close the browser
            browser.close()

        # Save DataFrame to CSV and display it
        df.to_csv("triesteHCP.csv", index=False)
        st.success("Data scraped successfully!")
        st.write(df)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="triesteHCP.csv",
            mime="text/csv"
        )
