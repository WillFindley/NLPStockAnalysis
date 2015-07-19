import re

def writeTableCreate(firstRow):
    
    fileO.write(
    'DROP TABLE IF EXISTS Tags;\n' + 
    'CREATE TABLE Tags (\n' +
    '   Id int NOT NULL PRIMARY KEY,\n' +
    '   TagName varchar(255),\n' +
    '   Count int\n' +
    ');\n'
    )


def writeRowInsert(fileO,row):

    row = re.split('(?<!\\\)"',row)
    tagName = '""'
    count = 0
    for thisElement in xrange(len(row)):
        if row[thisElement] == ' TagName=':
            tagName = '"' + row[thisElement+1] + '"'
        elif row[thisElement] == ' Count=':
            count = row[thisElement+1]
    fileO.write('INSERT INTO Tags VALUES ('+ row[1] + ',' + tagName + ',' + count + ');\n')


with open('Tags.xml','r') as fileI, open('Tags.sql','w') as fileO:
    # get rid of the first two lines that we won't use
    fileI.readline()
    tableLine = list(fileI.readline().strip())
    tableLine.insert(1,'/')
    end = ''.join(tableLine)
    
    writeTableCreate(fileO)

    row = fileI.readline().strip()
    while (row != end):
    
        writeRowInsert(fileO,row)

        row = fileI.readline().strip()

    fileI.close()
    fileO.close()
