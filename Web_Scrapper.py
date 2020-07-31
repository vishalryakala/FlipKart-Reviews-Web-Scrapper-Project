import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
from flask import Flask, render_template, request,jsonify

# initialising the flask app with the name 'app'
app = Flask(__name__)

@app.route('/',methods=['POST','GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        print('POST METHOD CALLED')
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            print('Entered Try')
            # opening a connection to Mongo
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            # connecting to the database called crawlerDB
            db = dbConn['FlipKartWebCrawlerDB']
            print('Made Connection')
            # searching the collection with the keyword entered
            reviews = db[searchString].find({})
            print('Search in DB complete')
            # if there is a collection with searched keyword and it has records in it
            if reviews.count() > 0:
                # show the results to user
                return render_template('results.html', reviews=reviews)
            else:
                # Preparing the URL to search the product on Flipkart
                flipkart_url = "https://www.flipkart.com/search?q="+ searchString
                #*** Using urllib to get webpage ***
                uClient = uReq(flipkart_url) # Requesting the webpage from the internet
                flipkartPage = uClient.read() # Reading the webpage
                uClient.close() # Closing the connection to the web server
                flipkart_html = bs(flipkartPage,"html.parser") # Parsing the webpage as HTML, using the html parser
                bigboxes = flipkart_html.findAll("div",{"class":"bhgxx2 col-12-12"})
                # Here, we are getting div which has class name as "bhgxx2 col-12-12"
                # We get a list of all the products on the flipkart page in bigboxes
                del bigboxes[0:3] # The first 3 members of the list do not contain relevant information. So, deleting them
                box = bigboxes[0] # taking the first iteration for demo
                productLink = "https://www.flipkart.com"+box.div.div.div.a['href'] # Extracting all actual product link
                #print(productLink)
                #*** Using requests to get web page ***
                prodRes = requests.get(productLink) # Getting the product page from server
                prod_html = bs(prodRes.text, "html.parser") # parsing the product page as HTML
                commentboxes = prod_html.find_all('div',{'class':"_3nrCtb"})
                #print(commentboxes)
                #print(len(commentboxes))


                # create a collection with name as search string. (Collection is a table in MongoDB)
                table = db[searchString]
                reviews = []  # initializing an empty list for reviews
                #  iterating over the comment section to get the details of customer and their comments
                for commentbox in commentboxes:
                    try:
                        name = commentbox.div.div.find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text
                    except:
                        name = 'No Name'
                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = 'No Rating'
                    try:
                        commentHead = commentbox.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'
                    try:
                        comtag = commentbox.div.div.find_all('div', {'class': ''})
                        custComment = comtag[0].div.text
                    except:
                        custComment = 'No Customer Comment'

                    # save the details to a dictionary
                    mydict = {"Product": searchString,
                               "Name": name,
                               "Rating": rating,
                               "CommentHead": commentHead,
                               "Comment": custComment}
                    x = table.insert_one(mydict)  # insertig the dictionary containing the rview comments to the collection
                    reviews.append(mydict)  # appending the comments to the review list
                print(mydict)
                return render_template('results.html', reviews=reviews)  # showing the review to the user
        except:
            return 'something is wrong'
        else:
            return render_template('index.html')
    return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000,debug=True)