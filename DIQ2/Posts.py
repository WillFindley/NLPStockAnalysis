import re

def writeTableCreate(firstRow):
    
    fileO.write(
    'DROP TABLE IF EXISTS Posts;\n'
    'CREATE TABLE Posts (\n'
    '   Id int NOT NULL PRIMARY KEY,\n'
    '   Tags varchar(255),\n'
    '   PostTypeId int,\n'
    '   Score int, \n'
    '   OwnerUserId int, \n'
    '   AcceptedAnswerId int, \n'
    '   CreationDate datetime(6) \n'
    ');\n'
    )


def writeRowInsert(fileO,row):

    row = re.split('(?<!\\\)"',row)
    tags = 'NULL'
    postTypeId = 'NULL'
    score = 'NULL'
    ownerUserId = 'NULL'
    acceptedAnswerId = 'NULL'
    creationDate = 'NULL'
    for thisElement in xrange(len(row)):
        if row[thisElement] == ' Tags=':
            tags = '"' + row[thisElement+1] + '"'
        elif row[thisElement] == ' PostTypeId=':
            postTypeId = row[thisElement+1]
        elif row[thisElement] == ' Score=':
            score = row[thisElement+1]
        elif row[thisElement] == ' OwnerUserId=':
            ownerUserId = row[thisElement+1]
        elif row[thisElement] == ' AcceptedAnswerId=':
            acceptedAnswerId = row[thisElement+1]
        elif row[thisElement] == ' CreationDate=':
            formatTime = row[thisElement+1].split('T')
            formatTime.insert(1,' ')
            formatTime = ''.join(formatTime)
            creationDate = '"' + formatTime + '"'
    fileO.write('INSERT INTO Posts VALUES ('+ row[1] + ',' + tags  + ',' + postTypeId + ',' + score + ',' + ownerUserId + ',' + acceptedAnswerId + ',' + creationDate + ');\n')


with open('Posts.xml','r') as fileI, open('Posts.sql','w') as fileO:
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
