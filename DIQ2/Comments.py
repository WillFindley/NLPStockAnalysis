import re

def writeTableCreate(firstRow):
    
    fileO.write(
    'DROP TABLE IF EXISTS Comments; \n' 
    'CREATE TABLE Comments ( \n'
    '   Id int NOT NULL PRIMARY KEY, \n'
    '   CreationDate datetime(6) \n'
    ');\n'
    )


def writeRowInsert(fileO,row):

    row = re.split('(?<!\\\)"',row)
    creationDate = 'NULL'
    for thisElement in xrange(len(row)):
        if row[thisElement] == ' CreationDate=':
            formatTime = row[thisElement+1].split('T')
            formatTime.insert(1,' ')
            formatTime = ''.join(formatTime)
            creationDate = '"' + formatTime + '"'
    if creationDate == 'NULL':
        print row[1]
    fileO.write('INSERT INTO Comments VALUES ('+ row[1] + ',' + creationDate + ');\n')


with open('Comments.xml','r') as fileI, open('Comments.sql','w') as fileO:
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
