import requests
from bs4 import BeautifulSoup
import re
import time
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request

app = Flask(__name__)
app.app_context().push()

#Configure the PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://debarunlahiri:password@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ScrpMainSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_url = db.Column(db.Text)
    site_name = db.Column(db.Text)
    flag = db.Column(db.Integer)

    def __init__(self, site_url, site_name, flag):
        self.site_url = site_url
        self.site_name = site_name
        self.flag = flag

    
class ScrpSubSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_site_id = db.Column(db.Integer)
    site_url = db.Column(db.Text)
    is_url_broken = db.Column(db.Integer)
    flag = db.Column(db.Integer)

    def __init__(self, main_site_id, site_url, is_url_broken, flag):
        self.main_site_id = main_site_id
        self.site_url = site_url
        self.is_url_broken = is_url_broken
        self.flag = flag

    
    

def remove_duplicates(l):
    """Remove duplicates and unURL string"""
    links = []
    for item in l:
        match = re.search("(?P<url>https?://[^\\s]+)", item)
        if match is not None:
            links.append(match.group("url"))
    return links

def initWebScraper(soup):
    """Initialize web scraper"""
    data = []
    links = []

    for link in soup.find_all('a', href=True):
        data.append(str(link.get('href')))
    flag = True

    links.extend(remove_duplicates(data))
    while flag:
        try:
            for link in links:
                for j in soup.find_all('a', href=True):
                    temp = []
                    source_code = requests.get(link)
                    soup = BeautifulSoup(source_code.content, 'lxml')
                    temp.append(str(j.get('href')))
                    print(temp)
                    links.extend(remove_duplicates(temp))
                    if len(links) > 162: # set limitation to number of URLs
                        break
                if len(links) > 162:
                    break
            if len(links) > 162:
                break
        except Exception as e:
            print(e)
            if len(links) > 162:
                break

    for url in links:
        print(url)
        
    return links

def checkIdPresence(id):
    """Check if the ID is present in the database"""
    scrptMainSite = ScrpSubSite.query.filter_by(main_site_id=id).first()
    if scrptMainSite is None:
        return False
    return True

def main():
    scrptMainSites = ScrpMainSite.query.all()
    
    for scrptMainSite in scrptMainSites:
        print(scrptMainSite.id)
        if checkIdPresence(scrptMainSite.id) == False:
            source_code = requests.get(scrptMainSite.site_url)
            soup = BeautifulSoup(source_code.content, 'lxml')
            links = initWebScraper(soup)
            for link in links:
                try:
                    scrptSubSite = ScrpSubSite(scrptMainSite.id, link, 0, 1)
                    db.session.add(scrptSubSite)
                    db.session.commit()
                    print("Record added successfully.")
                except Exception as e:
                    db.session.rollback()  # Rollback the transaction if an error occurs
                    print("Error:", e)
            else:
                print("Record already exists.")



if __name__ == "__main__":
    main()
