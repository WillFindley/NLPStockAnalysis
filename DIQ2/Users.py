import re

def writeTableCreate(firstRow):
    
    fileO.write(
    'DROP TABLE IF EXISTS Users;\n' + 
    'CREATE TABLE Users (\n' +
    '   Id int NOT NULL PRIMARY KEY,\n' +
    '   Reputation int\n' +
    ');\n'
    )


def writeRowInsert(fileO,row):

    row = re.split('(?<!\\\)"',row)
    reputation = 'NULL'
    for thisElement in xrange(len(row)):
        if row[thisElement] == ' Reputation=':
            reputation = row[thisElement+1]
    fileO.write('INSERT INTO Users VALUES ('+ row[1] + ',' + reputation + ');\n')


with open('Users.xml','r') as fileI, open('Users.sql','w') as fileO:
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
