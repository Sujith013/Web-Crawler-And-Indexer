The crawler.py is the main function that starts crawling for links from the url given and it uses a HTML parser to parse the text and send it to the indexer. 
The crawler function takes two arguments namely --url and --max. URL is the base url and max is the maximum number of documents/ files to be parsed. The default values are set, but these can be overridden if needed. Eg: Run the program in the terminal as

"python crawler.py --url https://spectrum.library.concordia.ca/ --max 1000"

The crawler would send the results to indexer and the indexer would create the postings list and the metadata for the documents. The indexer then saves the index created to "index.json" file. 

If you want to search for terms from the index, just run the indexer.py program as "python indexer.py"
The program will run a infinite while loop where you can enter query terms and type 'exit' to quit the program. For each query, you get the results of the postings list with frequency of the term.

Now, the cluster.ipynb file contains all the clustering experiments done and also contains the results for the top 50 terms per cluster for K = 2,10 and 20. The output of the same is attached in the demo file. The list is extensive as 50 words are printed for each of the individual clusters for 3 experiments. Detailed analysis on the results are provided in the report. 

To run the cluster.ipynb, you simply need to have a jupyter notebook extension in your IDE and a python environment. Just run each of the cells. I have also added the necessary pip installations on the first cell of the code. 

All requirements are specified on the requirements.txt file. You may install the packages as needed.