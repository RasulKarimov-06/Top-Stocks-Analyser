# Top-Stocks-Analyser (Visual Studio)
This program scrapes real time financial data, metrics and ratios of the top companies from the S&amp;P 500, and scores them on how attractive each investment is.

Optimisation and APIs:

A few technical announcements, as of making this code I am using the sites Yahoo Finance, Finviz and Financial Modeling Prep (FMP) to scrape data for this program. The API I use for FMP is the free version so it is limited to 300 requests per day, if you want to unlock the full capabilities of screening all 500 stocks I advise you to use your own API key or purchase a subscription from the FMP to have access to upwards of 300 requests per minute.

I am aware of the speed issues of screening the stocks whilst it is a lot faster than manual observation I have used concurrent and parallel processing to read and scrape multiple ticker data at the same time to improve speed, it is still a bit slow especially for large screenings (i.e hundreds of stocks), but that is something to be improved. Other than that, the code works as theorised as long as you have the correct API key to fill in the placeholder in my code. 

I AM NOT A FINANCIAL ADVISOR, THIS IS NOT FINANCIAL ADVICE.

SCORING GUIDE ON MY INVESTMENT THESIS:
Scoring of stocks is based on my own investment strategies which looks for companies that have high/consistent growth, strong financial health (i.e. low debt, good free cash flow, and great liquidity) and great valuation (P/E, PEG, and P/S). The point system is out of 10. I aim to solve the problem of the inconvienience to look through all data of these 500 companies consistently.

For the growth analysis my main red flag is stagnant companies, if a company fails to achieve revenue growth of at least 50% within 5 years there will be 0 out of 3 points awarded. Consistent growth is a green flag, but inconsistent growth is not a dealbreaker as macro-economic events do have an impact on certain years causing some blips in revenue. As a result if a company has good growth but inconsistencies they are awarded 1.5 out of 3 points. And if they have great/consistent growth they are awarded the full 3 points.

For the financial health analysis my main metrics I use are the Debt/Equity ratio, Free Cash Flow, Current Ratios and Quick ratios. Normally a lot of these ratios go hand in hand with one another (i.e. Debt/Equity and Current Ratio), so I didn't feel obligated to prohibit any earned points just because Debt/Equity ratio was beyond my liking as the system would already dock points because the company would usually fail meeting my desired targets for Current Ratios and Quick Ratios too. I instead just allocated each metric a point. If a firm has a Debt/Equity below 1 that will be awarded 1 point, if a firm has a positive free cash flow that will be awarded 1 point, if a firm has Current Ratio above 1.2 that will be awarded 1 point and if a firm has a Quick Ratio above 1 that will be awarded 1 point. Of course the signficane/level of each metric recorded is also important to consider so the stock screener also displays all the growth metrics, financial metrics and valuation metrics alongside the score for human judgement to be used. These levels are arbitrary and are just my likings, you are free to change them if you will.

For the valuation analysis, one of my favourite measurements is the PEG ratio. Whilst the P/E is useful it is heavily industry specific and I believe does not tell a good story on the company's valuation as companies that are growing massively can certainly meet and surpass the hype/expectations brought about by typically "overvalued" P/E figures even for the industry, for exmaple. NVDA. The PEG accounts for the expected earnings growth of the company allowing for P/E to also consider if a company is growing massively is the valuation still worth it. PEG of under 1 is undervalued and is the golden stock, companies only need to meet their expected earnings to grow in share price and as a result are awarded 3 points in the valuation scoring. PEG of 1-2 is fairly valued and are awarded 2 points. PEG of 2-3 are slightly overvalued, it is still very possible to see share price rise especially if companies are awarded big contracts, make great breakthroughs in their operations but is a lot more unlikely and requires a lot more research and supervision than the formers before making a decision to invest, thus awarding 1 point.

I also use the Price to Sales ratio for valuation scoring, as many companies traded on the stock exchange don't have official earnings yet but still achieve great investor sentiment in financial markets. Without earnings P/E and PEG cannot be used so I use their PE (AKA the absent/negative P/E) to not only calculate PEG but to evaluate whether Price to Sales ratio (P/S) should be used instead. However, these companies are more risky and P/S is very industry specific so whilst I gave a range for an appropriate P/S ratio level any company that does pass the threshold (i.e. is below it) is not of the same value as a PEG<1, and will instead earn 1 point to offset the risk associated with growing but non-profitable companies.

Nevertheless, individual research is the most important so whilst I give scoring for the stocks, I also display all metrics for you to evaluate and research whether these scorings or "red flags" can be excused or not. I am not a financial advisor, this is not financial advice, this is purely for educational purposes.


Many thanks to you for taking the time to read this and use my code. Happy screening!



