import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

import subprocess

import os
os.system('playwright install')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Convert the HCP to integers, display, save

def convert_display_save(df):
    df2 = df.copy()
    # Convert "Handicap" column to float by replacing commas with dots
    df2["Handicap"] = df2["Handicap"].str.replace(",", ".").astype(float)
    
    # Step 2: Merge "Cognome" and "Nome" into a single column "FullName"
    df2["FullName"] = df2["Cognome"] + " " + df2["Nome"]
    
    # Drop the old "Cognome" and "Nome" columns if no longer needed
    df2 = df2[["Handicap", "FullName"]]
    
    # Reverse the column order of df2
    df2 = df2[["FullName", "Handicap"]]
    
    # Save DataFrame to CSV and show it on screen
    df2.to_csv("triesteHCP.csv", index=False)
    st.success("Data scraped successfully!")
    
    # Display the DataFrame with full width
    st.dataframe(df2, use_container_width=True)
    
    st.download_button(
        label="Download CSV",
        data=df2.to_csv(index=False),
        file_name="triesteHCP.csv",
        mime="text/csv"
        )
    # Display the updated DataFrame
    # Remove rows where Handicap >= 54
    df2 = df2[df2["Handicap"] < 54]
    
    # Plot histogram of "Handicap" values
    plt.figure(figsize=(10, 6)) 
    count, bins, ignored = plt.hist(df2["Handicap"], bins=10, density=True, alpha=0.6, color='skyblue', edgecolor='black')
    
    # Fit a normal distribution to the data
    mean, std_dev = norm.fit(df2["Handicap"])
    
    # Plot the Gaussian fit
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mean, std_dev)
    plt.plot(x, p, 'k', linewidth=2, label=f'Gaussian fit\nMean: {mean:.2f}, Std Dev: {std_dev:.2f}')
    
    # Add labels and title
    plt.xlabel('Handicap')
    plt.ylabel('Density')
    plt.title('Golf Club Handicap distribution (only players with HCP <54)')
    plt.legend()
    
    # Display the plot in Streamlit
    st.pyplot(plt)


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
            
            # Check if login was successful by looking for an element that indicates success
            if "invalidi" in page.content():  # Adjust this condition based on actual response
                st.error("Incorrect username or password. Please try again.")
            else:
                page.goto(secondurl)

                # Scrape left pages (1-10)
                for i in range(1, 11):
                    if i > 1:  # Navigate for pages 2-10
                        # Get initial table content
                        initial_content = page.inner_html('#cpCorpo_gv_Handicap')
                        
                        # Now i click to get the new page
                        page.locator("#cpCorpo_gv_Handicap").get_by_role("cell", name=str(i), exact=True).click()
                        # now I wait till the content changes
                        page.wait_for_function(f'document.querySelector("#cpCorpo_gv_Handicap").innerHTML != `{initial_content}`')
                        
                        #page.wait_for_selector('#cpCorpo_gv_Handicap')
                        #page.wait_for_selector('#cpCorpo_gv_HandicapNZ')
                        
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
                        # Now i get the new pages from 2 ... from the right part of the page
                        page.locator("#cpCorpo_gv_HandicapNZ").get_by_role("cell", name=str(i), exact=True).click()

                        # now I wait till the content changes
                        page.wait_for_function(f'document.querySelector("#cpCorpo_gv_HandicapNZ").innerHTML != `{initial_content}`')
                        
                        #page.wait_for_selector('#cpCorpo_gv_HandicapNZ')
                        #page.wait_for_selector('#cpCorpo_gv_Handicap')
                    
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
                convert_display_save(df)
