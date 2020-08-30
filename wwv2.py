#encoding: utf-8
import requests, os, codecs, shutil, os.path, sys, time, uuid, ssl
from bs4 import BeautifulSoup
from zipfile import ZipFile

baseURL = "https://m.wuxiaworld.co/"
novelURL = "Renegade-Immortal"

def generate(html_files):
    pccount = 0
    epub = ZipFile(novelURL + ".epub", "w")
    epub.writestr("mimetype", "application/epub+zip")
    epub.writestr("META-INF/container.xml", '''<container version="1.0"
                  xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
          <rootfiles>
            <rootfile full-path="OEBPS/Content.opf" media-type="application/oebps-package+xml"/>
          </rootfiles>
        </container>''')
    uniqueid = uuid.uuid1().hex
    index_tpl = '''<package version="3.1"
    xmlns="http://www.idpf.org/2007/opf" unique-identifier="''' + uniqueid + '''">
            <metadata>
                %(metadata)s
            </metadata>
            <manifest>
                %(manifest)s
                <item href="cover.jpg" id="cover" media-type="image/jpeg" properties="cover-image"/>
            </manifest>
            <spine>
                <itemref idref="toc"/>
                %(spine)s
            </spine>
        </package>'''
    manifest = ""
    spine = ""
    metadata = '''<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">%(novelname)s</dc:title>
        <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:ns0="http://www.idpf.org/2007/opf" ns0:role="aut" ns0:file-as="Unbekannt">%(author)s</dc:creator>
        <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>
        <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/">%(uuid)s"</dc:identifier>''' % {
        "novelname": novelURL, "author": "none", "uuid": uniqueid}
    toc_manifest = '<item href="toc.xhtml" id="toc" properties="nav" media-type="application/xhtml+xml"/>'
    
    for i, html in enumerate(html_files):
        newhtml = html.replace("?", "")
        newerhtml = newhtml.replace("\"","")
        newesthtml = newerhtml.replace("*","")
        basename = os.path.basename(newerhtml)
        #print("DBG File Name " + basename)
        manifest += '<item id="file_%s" href="%s" media-type="application/xhtml+xml"/>' % (
                      i+1, basename)
        spine += '<itemref idref="file_%s" />' % (i+1)
        
        epub.write(newesthtml, "OEBPS/"+basename)

    epub.writestr("OEBPS/Content.opf", index_tpl % {
        "metadata": metadata,
        "manifest": manifest + toc_manifest,
        "spine": spine,
        })

    #Generates a Table of Contents + lost strings
    toc_start = '''<?xml version='1.0' encoding='utf-8'?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
        <head>
            <title>%(novelname)s</title>
        </head>
        <body>
            <section class="frontmatter TableOfContents">
                <header>
                    <h1>Contents</h1>
                </header>
                <nav id="toc" role="doc-toc" epub:type="toc">
                    <ol>
                    %(toc_mid)s
            %(toc_end)s'''
    toc_mid = ""
    toc_end = '''</ol></nav></section></body></html>'''
    
    for i, y in enumerate(html_files):
        pccount += 1
        print(str(round(pccount/len(html_files) * 100,2)) + "%", end="\r")
        
        ident = 0
        html = html_files[i].replace("?", "")
        bruhhtml = html.replace("\"", "")
        oldhtml = html.replace("*", "")
        newhtml = oldhtml.replace(".\\tmp\\", "")
        chapter = find_between(oldhtml)
        chapter = str(chapter)
        toc_mid += '''<li class="toc-Chapter-rw" id="num_%s">
            <a href="%s">%s</a>
            </li>''' % (i, newhtml, chapter)
        
    print("\n")
    
    epub.writestr("OEBPS/toc.xhtml", toc_start % {"novelname": novelURL, "toc_mid": toc_mid, "toc_end": toc_end})
    epub.close()
    
    for i, y in enumerate(html_files):
        ident = 0
        html = html_files[i].replace("?", "")
        newhtml = html.replace("\"", "")
        newerhtml = html.replace("*", "")
        chapter = find_between(newerhtml)
        chapter = str(chapter)
        toc_mid += '''<li class="toc-Chapter-rw" id="num_%s">
            <a href="%s">%s</a>
            </li>''' % (i, newhtml, chapter)
    
def getURLS(novel):
    urlDict = {}
    res = requests.get(baseURL + novel + "/all.html")
    soup = BeautifulSoup(res.text, features="html.parser")
    chapters = soup.find(class_="chapter-list")
    for x in chapters.findAll("a"):
        chName = x.find("p").decode_contents()
        chName = chName.replace("?", "")
        chName = chName.replace("\"", "")
        chName = chName.replace(":", "")
        urlDict[chName] = x["href"]
    
    return urlDict

def getChapter(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, features="html.parser")
    #print("DBG URL " + url)
    content = soup.find(class_="chapter-entity")

    for x in content.findAll("script"):
        x.decompose()
    
    for div in content.findAll("div"):
        div.decompose()

    for ins in content.findAll("ins"):
        ins.decompose()

    return content

def find_between(file):
    f = open(file, "r", encoding = "utf8")
    soup = BeautifulSoup(f, 'html.parser')
    return soup.title.string

def writeXHTML(chapterName, content):
    
    converted = ""
    contentList = list(content.strings)
    for x in contentList:
        if "\n" in x:
            contentList[contentList.index(x)] = contentList[contentList.index(x)].replace("\n", "")

##    converted += ("""<html xmlns="http://www.w3.org/1999/xhtml">
##                    <head>
##                    <meta charset="urf-8"/>
##                        <title>""" + chapterName + """</title>
##                    </head>
##                    <body><div>
##                    """)
##
##    converted += ("<h1>" + chapterName + "</h1>")
##    
##    for index, lines in enumerate(contentList):            
##        converted += ("<p>" + lines + "</p>")
##
##    converted += ("</div></body></html>")
##    return converted
    test = chapterName.replace("?", "")
    oldtest = test.replace("\"", "")
    newtest = oldtest.replace("*", "")
    #print("DBG DIR PATH " + os.getcwd() + "\\" + newtest + ".xhtml")
    file = codecs.open(os.getcwd() + "\\tmp\\" + newtest + ".xhtml", "a+", "utf-8")
    file.write("""<html xmlns="http://www.w3.org/1999/xhtml">
                    <head>
                    <meta charset="urf-8"/>
                        <title>""" + chapterName + """</title>
                    </head>
                    <body><div>
                    """)

    file.write("<h1>" + chapterName + "</h1>")
    
    for index, lines in enumerate(contentList):            
        file.write("<p>" + lines + "</p>")
    file.write("</div></body></html>")
    file.close()     

if "/" in novelURL:
    print("""
================================================================
#                                                              #
#            Error, please ensure that there are               #
#                no slashes in the novelURL                    #
#                                                              #
================================================================
""")
else:
    urlDict = getURLS(novelURL)
    html_files = []
    count = 0
    print("""
======================================
#                                    #
#     Getting chapter contents...    #
#                                    #
======================================

""")
    complete = len(urlDict)
    if not os.path.exists(os.getcwd() + "\\tmp"):
        print("nope")
        os.mkdir("tmp")
    for item in urlDict:
        writeXHTML(item, getChapter(baseURL + urlDict[item]))
        html_files.append(".\\tmp\\" + item + ".xhtml")
        count += 1
        pc = str(round(count/complete * 100,2))
        print(pc + "%", end="\r")
    print("""\n
======================================
#                                    #
#         Compiling Files...         #
#                                    #
======================================
\n""")
    generate(html_files)
    os.system("del .\\tmp\\*.xhtml")

    print("#############  Complete! #############\n")
