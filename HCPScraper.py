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
    #Convert "Handicap" column to float by replacing commas with dots
    df2["Handicap"] = df2["Handicap"].str.replace(",", ".").astype(float)
    
    # Step 2: Merge "Cognome" and "Nome" into a single column "FullName"
    #df2["FullName"] = df2["Cognome"] + " " + df2["Nome"]
    
    # Drop the old "Cognome" and "Nome" columns if no longer needed
    #df2 = df2[["Handicap", "FullName"]]
    
    # Reverse the column order of df2
    df2 = df2[["Cognome", "Nome", "Handicap"]]
    
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
    # --------------------------------  GRAPH 1 --------------------------------
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

    # ------------------------------    GRAPH 2 -------------------
    # Remove rows where Handicap >= 54
    df3 = df2[df2["Handicap"] <= 36.0]
    
    # Plot histogram of "Handicap" values
    plt.figure(figsize=(10, 6)) 
    count, bins, ignored = plt.hist(df3["Handicap"], bins=10, density=True, alpha=0.6, color='skyblue', edgecolor='black')
    
    # Fit a normal distribution to the data
    mean, std_dev = norm.fit(df3["Handicap"])
    
    # Plot the Gaussian fit
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mean, std_dev)
    plt.plot(x, p, 'k', linewidth=2, label=f'Gaussian fit\nMean: {mean:.2f}, Std Dev: {std_dev:.2f}')
    
    # Add labels and title
    plt.xlabel('Handicap')
    plt.ylabel('Density')
    plt.title('Golf Club Handicap distribution (only players with HCP <36)')
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

    
                # ------------------------- New Code 13 August 2025 ----------------
                # Scrape left pages (1–10)
                for i in range(1, 11):
                    if i > 1:
                        # snapshot current table HTML
                        initial_content = page.inner_html('#cpCorpo_gv_Handicap')
                        # click the pager *link* for page i (not cells)
                        pager_link = page.locator("#cpCorpo_gv_Handicap").get_by_role("link", name=str(i))
                        if pager_link.count() > 0:
                            pager_link.first.click()
                            page.wait_for_function(
                                "([sel, html]) => document.querySelector(sel).innerHTML !== html",
                                arg=["#cpCorpo_gv_Handicap", initial_content]
                            )
                        # If there's no link (already on that page), do nothing.
                
                    html2 = page.inner_html('#cpCorpo_gv_Handicap')
                    table = BeautifulSoup(html2, "html.parser")
                    column_data = table.find_all("tr")
                    for row in column_data[1:]:
                        row_data = row.find_all("td")
                        individual_row_data = [data.text.strip() for data in row_data]
                        if len(individual_row_data) == len(df.columns):
                            df.loc[len(df)] = individual_row_data
                
                st.subheader("First 200 Golfers Scraped ...")
                
                # Scrape right pages (1–7)
                for i in range(1, 8):
                    if i > 1:
                        # snapshot current table HTML (right grid)
                        initial_content_nz = page.inner_html('#cpCorpo_gv_HandicapNZ')
                        # click the pager *link* for page i (not cells)
                        pager_link_nz = page.locator("#cpCorpo_gv_HandicapNZ").get_by_role("link", name=str(i))
                        if pager_link_nz.count() > 0:
                            pager_link_nz.first.click()
                            page.wait_for_function(
                                "([sel, html]) => document.querySelector(sel).innerHTML !== html",
                                arg=["#cpCorpo_gv_HandicapNZ", initial_content_nz]
                            )
                
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
