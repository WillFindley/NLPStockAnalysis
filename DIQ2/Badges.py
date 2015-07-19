


with open('Badges.xml','r') as fileI, open('Badges.sql','w') as fileO:
    # get rid of the first two lines that we won't use
    fileI.readline()
    fileI.readline()

    firstRow = fileI.readline()
    tableCreate = writeTableCreate(firstRow)
