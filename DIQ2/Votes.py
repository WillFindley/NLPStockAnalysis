import re

def writeTableCreate(firstRow):
    
    fileO.write(
    'DROP TABLE IF EXISTS Votes;\n' + 
    'CREATE TABLE Votes (\n' +
    '   Id int NOT NULL PRIMARY KEY,\n' +
    '   PostId int,\n' +
    '   VoteTypeId int\n' +
    ');\n'
    )


def writeRowInsert(fileO,row):

    row = re.split('(?<!\\\)"',row)
    postId = 'NULL'
    voteTypeId = 'NULL'
    for thisElement in xrange(len(row)):
        if row[thisElement] == ' PostId=':
            postId = row[thisElement+1]
        elif row[thisElement] == ' VoteTypeId=':
            voteTypeId = row[thisElement+1]
    fileO.write('INSERT INTO Votes VALUES ('+ row[1] + ',' + postId + ',' + voteTypeId + ');\n')


with open('Votes.xml','r') as fileI, open('Votes.sql','w') as fileO:
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
