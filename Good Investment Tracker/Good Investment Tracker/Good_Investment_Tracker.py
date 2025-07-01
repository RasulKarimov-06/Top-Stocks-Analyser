import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox
import threading


def launch_gui(data):
    #creates main GUI window
    root = tk.Tk()
    root.title("S&P 500 Screener Results")

    #Get the user's full screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    #sets the window to full screen size
    root.geometry(f"{screen_width}x{screen_height}")

    #creates a container frame that holds the canvas and scrollbar
    container = ttk.Frame(root)
    container.pack(fill='both', expand=True)

    #allows us to scroll customer widgets
    canvas = tk.Canvas(container)
    canvas.pack(side='left', fill='both', expand=True)

    #vertical scrollbar attached to canvas
    scrollbar_y = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
    scrollbar_y.pack(side='right', fill='y')

    #horizontal scrollbar attached
    scrollbar_x = ttk.Scrollbar(root, orient='horizontal', command=canvas.xview)
    scrollbar_x.pack(side='bottom', fill='x')

    canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    #creates a frame inside the canvas where the table will go
    frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor='nw')

    #this function updates the scroll region of the canvas whenever the size frame changes
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox('all'))
    frame.bind('<Configure>', on_configure)

    #If data can't be fetched it displays this
    if not data:
        tk.Label(frame, text="No data to display").pack()
        return

    #grabs the column names from the keys of the first dictionary in the list
    columns = list(data[0].keys())
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    # Calculate widths dynamically:
    # Make sector column wider (about 1.5x normal width)
    base_col_width = int(screen_width / (len(columns) + 0.5))  # Add 0.5 to denominator to reduce width overall
    for col in columns:
        if col == "Sector":
            tree.column(col, width=int(base_col_width * 1.5), anchor='center')
        else:
            tree.column(col, width=base_col_width, anchor='center')

    # Set fonts smaller and row height tighter
    style = ttk.Style()
    style.configure("Treeview.Heading", font=('Arial', 9, 'bold'))
    style.configure("Treeview", font=('Arial', 8), rowheight=18)

    #set column headings
    for col in columns:
        tree.heading(col, text=col)

    # Helper to format large numbers with commas
    def format_value(col, val):
        if col == "Free Cash Flow":
            try:
                return f"{int(val):,}"
            except Exception:
                return val
        else:
            return val
    
    #inserts each row of data into the table
    for row in data:
        values = [format_value(col, row.get(col, '')) for col in columns]
        tree.insert('', 'end', values=values)

    tree.pack(fill='both', expand=True)
    #starts the GUI event loop
    root.mainloop()

#Scrapes data of tickers and their respective sectors from wikipedia
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)[0]
    # Returns a dictionary: {ticker: sector}
    return dict(zip(table['Symbol'], table['GICS Sector']))

#The FMP API key, used to scrape growth data and financial ratios for the program
API_KEY = 'YOUR API KEY'

def get_5yr_revenue_fmp(ticker):
    #Uses API key and the ticker symbol to fetch growth data
    url = f'https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=5&apikey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        #error handling
        print(f"Error fetching data for {ticker}: Status code {response.status_code}")
        return None
    data = response.json()
    revenues = {}
    #Cycles through each revenue figures of the 5 year recordings of the company
    for entry in data:
        year = entry.get('date', '')[:4]
        revenue = entry.get('revenue')
        if revenue is not None:
            revenues[year] = revenue
    if len(revenues) < 5:
        print(f"Not enough revenue data for {ticker}")
        return None
    return dict(sorted(revenues.items()))

#checks to see if the company is growing and if the growth is consistent
def growth_score_and_consistency(revenue_dict):
    years = sorted(revenue_dict.keys())
    revenues = [revenue_dict[year] for year in years]

    growth = ((revenues[-1] - revenues[0]) / revenues[0]) * 100
    growth = round(growth, 2)

    #My investment plan places more priority on high growth than consistency
    # So if total growth <= 50%, no points at all
    if growth <= 50:
        return 0.0, growth

    # Assign 1.5 points for absolute growth > 50
    score = 1.5

    # Check consistency: no year with decline
    consistent = True
    for i in range(1, len(revenues)):
        if revenues[i] < revenues[i - 1]:
            consistent = False
            break

    # Assign additional 1.5 points if consistent
    if consistent:
        score += 1.5

    return score, growth

#Yfinance is another tool I use, this is to grab the data needed to identify top S&P 500 companies
def fetch_market_cap(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        return (ticker, market_cap)
    except Exception:
        return (ticker, None)

#responsible for selecting the top companies based on market cap
def get_top_n_by_market_cap(tickers, number):
    #dictionary assigned to store pair values of tickers and their market cap
    caps = {}

    #Uses a thread pool to parrellise the process of fetching market caps, since sequentially is very slow for Yahoo
    with ThreadPoolExecutor(max_workers=number) as executor:
        #submits a task for every ticker in the list to fetch market cap and returns it
        futures = {executor.submit(fetch_market_cap, t): t for t in tickers}
        #waits for each task to finish in the order they complete not the order started to process results immediately than waiting for everyone
        for future in as_completed(futures):
            #stores successful results in the dictionary
            ticker, cap = future.result()
            if cap is not None:
                caps[ticker] = cap

    sorted_tickers = sorted(caps.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_tickers[:number]]

#Uses the ticker and FMP API to fetch financial ratios
def get_financial_ratios(ticker):
    try:
        print(f"\nFetching data for: {ticker}")

        # 1. TTM Ratios, for D/E, Quick and Current Ratios
        ratios_url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={API_KEY}"
        ratios_resp = requests.get(ratios_url)
        ratios_data = ratios_resp.json()

        # 2. Cash Flow, for Free Cash Flow Figures
        cashflow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=1&apikey={API_KEY}"
        cash_resp = requests.get(cashflow_url)
        cash_data = cash_resp.json()

        # Check validity
        if not ratios_data or not isinstance(ratios_data, list) or len(ratios_data) == 0:
            print(f"{ticker}: No TTM ratio data.")
            return None
        if not cash_data or not isinstance(cash_data, list) or len(cash_data) == 0:
            print(f"{ticker}: No cash flow data.")
            return None

        # Extract the financial data
        result = {
            'debtToEquity': ratios_data[0].get("debtEquityRatioTTM"),
            'currentRatio': ratios_data[0].get("currentRatioTTM"),
            'quickRatio': ratios_data[0].get("quickRatioTTM"),
            'freeCashFlow': cash_data[0].get("freeCashFlow")
        }

        # Check if any of the key values are None
        if any(v is None for v in result.values()):
            print(f"{ticker}: Incomplete financial data from FMP")
            return None

        return result

    except Exception as e:
        print(f"⚠ Error fetching/parsing data for {ticker}: {e}")
        return None

#Evaluates the scoring based on how many financial metrics it passes
def financial_strength_score(data):
    try:
        dte = round(float(data['debtToEquity']), 2)
        fcf = round(float(data['freeCashFlow']), 2)
        cr = round(float(data['currentRatio']), 2)
        qr = round(float(data['quickRatio']), 2)
    except (TypeError, ValueError):
        return 0.0, ("N/A", "N/A", "N/A", "N/A")

    score = 0.0
    if dte < 1:
        score += 1
    if fcf > 0:
        score += 1
    if cr >= 1.2:
        score += 1
    if qr >= 1:
        score += 1

    return score, (dte, fcf, cr, qr)

#Whilst FMP has great scraping, Finviz has a lot better valuation figures so I chose to scrape here, no API needed
def get_finviz_valuation(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"{ticker}: Finviz request failed — HTTP {resp.status_code}")
        return None

    #parses the raw html using BeautifulSoup for easy navigation
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # The key stats are inside a table with no class but inside a div with id='quote-header-info'
    # Actually, Finviz main data is in the big table with class "snapshot-table2"
    table = soup.find("table", class_="snapshot-table2")
    if not table:
        print(f"{ticker}: Could not find Finviz snapshot table")
        return None

    data = {}
    # The table has rows with pairs of <td>: label and value
    tds = table.find_all("td")
    #the loop goes two at a time to get past the label and value each interval
    for i in range(0, len(tds), 2):
        key = tds[i].get_text(strip=True)
        val = tds[i+1].get_text(strip=True)
        data[key] = val
        #builds a data dictionary like {"P/E":"28.3", "PEG":"1.9",...}
    
    #helps convert text into numerical percentages
    def parse_pct(x):
        if x and x.endswith('%'):
            try:
                return float(x.strip('%'))
            except:
                return None
        return None

    #helps convert text into numbers
    def parse_num(x):
        try:
            return float(x.replace(',', '').replace('$', ''))
        except:
            return None
    
    #assigns variables to parse the actual values for safe extraction
    ps = parse_num(data.get("P/S"))
    pe = parse_num(data.get("P/E"))
    peg = parse_num(data.get("PEG"))
    eps5y = parse_pct(data.get("EPS next 5Y"))

    if pe is None and peg is None and eps5y is None:
        print(f"{ticker}: No valuation data parsed from Finviz")
        return None

    return {
        "ticker": ticker,
        "ps": ps,
        "pe": pe,
        "peg": peg,
        "eps_next_5y": eps5y
    }

#assigns scores to valuation metrics, I value PEG and P/S in my strategy
def score_valuation(val_data, sector):
    try:
        pe = val_data.get('pe')
        peg = val_data.get('peg')
        ps = val_data.get('ps')

        #some industries have different price to sales ratio averages
        industry_ps_benchmarks = {
            "Information Technology": 6.26,
            "Health Care": 1.85,
            "Consumer Staples": 1.12,
            "Financials": 2.23,
            "Consumer Discretionary": 1.62,
            "Energy": 0.85,
            "Industrials": 1.6,
            "Materials": 1.17,
            "Communication Services": 3.24,
            "Utilities": 0.41,
            "Real Estate": 3.86
        }

        # PEG scoring if P/E is available
        # I give better scores to undervalued companies,
        # then fairly valued, slightly overvalued and none for over 3 (overvalued)
        if pe is not None and pe > 0:
            if peg is not None:
                if peg < 1:
                    return 3
                elif peg < 2:
                    return 2
                elif peg < 3:
                    return 1
                else:
                    return 0
            return 0

        # Fallback to P/S if P/E is missing
        # Since non-earning companies are more risky I only award a max of one point
        # if it passes P/S benchmarks
        if ps is not None:
            industry_avg = industry_ps_benchmarks.get(sector)
            if industry_avg and ps <= 1.5 * industry_avg:
                return 1

        return 0

    except:
        return 0

#custom class that inherits from tk.Tk the basic Tkinter window class
class StockScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        #sets window title and dimensions
        self.title("S&P 500 Stock Screener")
        self.geometry("1100x600")

        # Input frame
        input_frame = tk.Frame(self)
        #adds vertical spacing
        input_frame.pack(pady=10)

        #Lbale what the input is expected, Entry takes in input, Button starts scanning process
        tk.Label(input_frame, text="Number of top S&P 500 companies to screen:").pack(side=tk.LEFT)
        self.num_companies_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.num_companies_var, width=5).pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Start Screening", command=self.start_screening).pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(pady=10)

        # Results frame with treeview (table)
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.columns = ['Ticker', 'Sector', 'Growth (%)', 'Debt/Equity', 'Free Cash Flow', 
                        'Current Ratio', 'Quick Ratio', 'P/E', 'PEG', 'P/S', 'Score (/10)']

        #Creates a Treeview table widget, sets each column title and centre aligns them,
        #packs it so it fills space inside the fram
        self.tree = ttk.Treeview(self.tree_frame, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the table
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    #function triggered when the screening button is pressed
    def start_screening(self):
        try:
            num = int(self.num_companies_var.get())
            if num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive integer.")
            return

        # Disable input while running
        # Resets the progress bar and clears input box
        self.progress['value'] = 0
        self.progress['maximum'] = num
        self.num_companies_var.set("")
        #Clears the table from any previous results
        for child in self.tree.get_children():
            self.tree.delete(child)

        #launches stock scanning logic in a background thread so GUI doesnt freeze while waiting for results
        threading.Thread(target=self.run_screening, args=(num,), daemon=True).start()

    #actual screening process
    def run_screening(self, number):
        #returns the dictionary of ticker and sector pairs
        ticker_sector_map = get_sp500_tickers()
        tickers = list(ticker_sector_map.keys())
        top = get_top_n_by_market_cap(tickers, number)

        #empty list to store final screened results
        results = []

        #loops through each ticker with its index i used to update progress bar
        for i, t in enumerate(top, 1):
            sector = ticker_sector_map.get(t, "Unknown")

            #fetching revenue and growth scores
            revenue_data = get_5yr_revenue_fmp(t)
            if not revenue_data:
                self.update_progress(i)
                continue
            growth_score, growth = growth_score_and_consistency(revenue_data)

            #fetching financial data and financial scores
            financial_data = get_financial_ratios(t)
            if not financial_data:
                self.update_progress(i)
                continue
            financial_score, (dte, fcf, cr, qr) = financial_strength_score(financial_data)

            #fetching valuation data and valuation scores
            valuation_data = get_finviz_valuation(t)
            if not valuation_data:
                self.update_progress(i)
                continue
            val_score = score_valuation(valuation_data, sector)

            total_score = growth_score + financial_score + val_score

            #appends all formatted data to the results list
            results.append({
                'Ticker': t,
                'Sector': sector,
                'Growth (%)': growth,
                'Debt/Equity': dte,
                'Free Cash Flow': f"{fcf:,}",  # Add commas here
                'Current Ratio': cr,
                'Quick Ratio': qr,
                'P/E': valuation_data.get('pe'),
                'PEG': valuation_data.get('peg'),
                'P/S': valuation_data.get('ps'),
                'Score (/10)': round(total_score, 2)
            })

            #moves progress bar forward after each company is scanned
            self.update_progress(i)
        
        #sorts companies by score in descending order, sends data to be displayed on table
        results_sorted = sorted(results, key=lambda x: x['Score (/10)'], reverse=True)
        self.display_results(results_sorted)

    #Updates progress bar to refelct how many companies been processed
    def update_progress(self, value):
        self.progress['value'] = value
    
    #populates the table with this function
    def display_results(self, results):
        for row in results:
            vals = [row[col] for col in self.columns]
            self.tree.insert('', 'end', values=vals)

if __name__ == "__main__":
    app = StockScannerApp()
    app.mainloop()