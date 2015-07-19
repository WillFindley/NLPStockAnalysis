# Get rank 5 tag for later use
SELECT TagName INTO @rank5Tag FROM
   (SELECT @row:=@row+1 AS RowNumber, Tags.TagName AS TagName FROM Tags, (SELECT @row:=0) r ORDER BY Tags.Count DESC) AS OrderedData
WHERE OrderedData.RowNumber=5;

# Add bounding tag characters
SET @rank5Tag = CONCAT('%&lt;', CAST(@rank5Tag AS CHAR),'&gt;%');  

SELECT COUNT(*) INTO @denominator FROM Posts;
SELECT COUNT(*) INTO @numerator FROM Posts WHERE Tags LIKE @rank5Tag; 
SET @answer1 = ROUND(@numerator/@denominator,10); 


SELECT ROUND(AVG(Score),12) INTO @meanAnswerScore FROM Posts WHERE PostTypeID=2; 
SELECT ROUND(AVG(Score),12) INTO @meanQuestionScore FROM Posts WHERE PostTypeID=1; 
SET @answer2 = ROUND(@meanAnswerScore - @meanQuestionScore,10); 


# find the average reptuations and total scores for everyone
SELECT ROUND(AVG(Reputation),12), ROUND(AVG(TotalScore),12) INTO @meanReputation, @meanTotalScore FROM 
   (SELECT Users.Reputation AS Reputation, ScoreTable.TotalScore AS TotalScore FROM Users 
       JOIN (SELECT OwnerUserId AS Id, SUM(Score) AS TotalScore FROM Posts GROUP BY OwnerUserId) AS ScoreTable 
       ON Users.Id = ScoreTable.Id 
   ) AS CorrelatedTable; 


# calculate the numerators and denominators for the pearson correlation
SELECT SUM(ReputationDeviation*TotalScoreDeviation), SQRT(SUM(POW(ReputationDeviation,2)))*SQRT(SUM(POW(TotalScoreDeviation,2))) 
   INTO @numerator, @denominator FROM 
   (SELECT Reputation-@meanReputation AS ReputationDeviation, TotalScore-@meanTotalScore AS TotalScoreDeviation FROM 
       (SELECT Users.Reputation AS Reputation, ScoreTable.TotalScore AS TotalScore FROM Users 
           JOIN (SELECT OwnerUserId AS Id, SUM(Score) AS TotalScore FROM Posts GROUP BY OwnerUserId) AS ScoreTable 
           ON Users.Id = ScoreTable.Id 
       ) AS CorrelatedTable 
   ) AS CorrelatedDeviationsTable; 

SET @answer3 = @numerator/@denominator; 


# get the average upvotes for the answers
SELECT ROUND(AVG(NumUpVotes),12) INTO @meanAnswer FROM
   (SELECT QATable.PostTypeId AS PostTypeId, UpVotesTable.NumUpVotes AS NumUpVotes FROM
      (SELECT Id, PostTypeId FROM Posts WHERE PostTypeId=1 OR PostTypeId=2) AS QATable
      JOIN (SELECT PostId AS Id, COUNT(*) AS NumUpVotes FROM Votes WHERE VoteTypeId=2 GROUP BY PostId) AS UpVotesTable
      ON QATable.Id=UpVotesTable.Id
   ) AS FinalCombinedTable
WHERE PostTypeId=2;

# get the average upvotes for the questions
SELECT ROUND(AVG(NumUpVotes),12) INTO @meanQuestion FROM
   (SELECT QATable.PostTypeId AS PostTypeId, UpVotesTable.NumUpVotes AS NumUpVotes FROM
      (SELECT Id, PostTypeId FROM Posts WHERE PostTypeId=1 OR PostTypeId=2) AS QATable
      JOIN (SELECT PostId AS Id, COUNT(*) AS NumUpVotes FROM Votes WHERE VoteTypeId=2 GROUP BY PostId) AS UpVotesTable
      ON QATable.Id=UpVotesTable.Id
   ) AS FinalCombinedTable
WHERE PostTypeId=1;

SET @answer4 = @meanAnswer-@meanQuestion;


# make a temporary table that has all of the time differences between questions and their accepted answers, as well as the hour of the question
DROP TABLE IF EXISTS TimeDiffTable;
CREATE TEMPORARY TABLE TimeDiffTable AS
   (SELECT HOUR(AnsweredQTable.QDate) AS QHour, 
      ROUND(((TO_SECONDS(ATable.ADate)-TO_SECONDS(AnsweredQTable.QDate))+(MICROSECOND(ATable.ADate)-MICROSECOND(AnsweredQTable.QDate))/1000000)/3600,12) AS TimeElapsedQA FROM
      (SELECT CreationDate AS QDate, AcceptedAnswerId AS Id FROM Posts WHERE AcceptedAnswerId IS NOT NULL) AS AnsweredQTable
      JOIN (SELECT CreationDate AS ADate, Id FROM Posts WHERE PostTypeId=2) AS ATable
      ON AnsweredQTable.Id=ATable.Id
   );

# make a temporary table that finds the total number of such questions for each question posting hour
DROP TABLE IF EXISTS HourTotalsTable;
CREATE TEMPORARY TABLE HourTotalsTable AS
   (SELECT QHour, count(*) AS NumRows FROM TimeDiffTable GROUP BY QHour);

# make a temporary table that finds the total number of such questions for each question posting hour
DROP TABLE IF EXISTS HourMediansTable;
CREATE TEMPORARY TABLE HourMediansTable (
   QHour int,
   Median double
);

# procedure to calculate the median for each question hour
DROP PROCEDURE IF EXISTS MEDIAN;
DELIMITER $$
CREATE PROCEDURE MEDIAN()
BEGIN
   SET @qHour = 0;
   Loop1: LOOP
      # this select statement actually calculates the median for this hour
      SELECT ROUND(AVG(OrderedData.TimeElapsedQA),12) INTO @median FROM
         (SELECT @row:=@row+1 AS RowNumber, TimeDiffTable.TimeElapsedQA AS TimeElapsedQA FROM TimeDiffTable, (SELECT @row:=0) r 
            WHERE TimeDiffTable.QHour=@qHour ORDER BY TimeDiffTable.TimeElapsedQA
         ) AS OrderedData, 
         (SELECT NumRows FROM HourTotalsTable WHERE HourTotalsTable.QHour=@qHour) AS TotalRows
      WHERE OrderedData.RowNumber in (FLOOR((TotalRows.NumRows+1)/2),FLOOR((TotalRows.NumRows+2)/2));
     
      INSERT INTO HourMediansTable VALUES (@qHour,@median);

      SET @qHour := @qHour + 1;
      IF (@qHour < 24) THEN 
         ITERATE Loop1;
      END IF;

      LEAVE Loop1;
   END LOOP Loop1;
END$$
DELIMITER ;

CALL MEDIAN();
SELECT MAX(Median)-MIN(Median) INTO @answer5 FROM HourMediansTable;


# create temporary table to hold the ordering of actions
DROP TABLE IF EXISTS ActionsTable;
CREATE TEMPORARY TABLE ActionsTable AS (SELECT * FROM 
   ((SELECT 'q' AS Action, CreationDate FROM Posts WHERE PostTypeId=1)
   UNION ALL
   (SELECT 'a' AS Action, CreationDate FROM Posts WHERE PostTypeId=2)
   UNION ALL
   (SELECT 'c' AS Action, CreationDate FROM Comments) ORDER BY CreationDate) AS t
);

SELECT COUNT(*) INTO @totalActions FROM ActionsTable;
DROP TABLE IF EXISTS UnconditionalTable;
CREATE TEMPORARY TABLE UnconditionalTable AS (
   SELECT @row:=@row+1 AS RowNumber, Action, Probability FROM
      (SELECT Action, ROUND(COUNT(*)/@totalActions,12) AS Probability FROM ActionsTable GROUP BY Action) AS t1,
      (SELECT @row:=0) AS r
);

SELECT MIN(CreationDate), MAX(CreationDate) INTO @firstDate, @lastDate FROM ActionsTable;

DROP TABLE IF EXISTS BeforeTable;
CREATE TEMPORARY TABLE BeforeTable AS (
   SELECT @row:=@row+1 AS RowNumber, ActionsTable.Action AS Action, ActionsTable.CreationDate AS CreationDate FROM ActionsTable, (SELECT @row := 0) r 
      WHERE ActionsTable.CreationDate<@lastDate ORDER BY CreationDate
);

DROP TABLE IF EXISTS AfterTable;
CREATE TEMPORARY TABLE AfterTable AS (
   SELECT @row:=@row+1 AS RowNumber, ActionsTable.Action AS Action, ActionsTable.CreationDate AS CreationDate FROM ActionsTable, (SELECT @row := 0) r 
      WHERE ActionsTable.CreationDate>@firstDate ORDER BY CreationDate
);

DROP TABLE IF EXISTS ConditionalTable;
CREATE TEMPORARY TABLE ConditionalTable (
   AfterAction char,
   BeforeAction char,
   Probability decimal(15,12)
);

# procedure to calculate conditional probabilities 
DROP PROCEDURE IF EXISTS MakeUCTable;
DELIMITER $$
CREATE PROCEDURE MakeUCTable()
BEGIN
   SET @rowNumberL1 = 1;
   Loop1: LOOP
      SELECT Action INTO @afterAction FROM UnconditionalTable WHERE RowNumber=@rowNumberL1;

      SELECT COUNT(*) INTO @numAfter FROM AfterTable WHERE Action=@afterAction;
      
      SET @rowNumberL2 = 1;
      Loop2: LOOP
         SELECT Action INTO @beforeAction FROM UnconditionalTable WHERE RowNumber=@rowNumberL2;
         
         SELECT ROUND(COUNT(*)/@numAfter,12) INTO @probability FROM 
            (SELECT RowNumber FROM AfterTable WHERE Action=@afterAction) AS t1, 
            (SELECT RowNumber FROM BeforeTable WHERE Action=@beforeAction) AS t2
            WHERE t1.RowNumber=t2.RowNumber;

         INSERT INTO ConditionalTable VALUES (@afterAction,@beforeAction,@probability);

         SET @rowNumberL2 := @rowNumberL2 + 1;
         IF (@rowNumberL2 < 4) THEN 
            ITERATE Loop2;
         END IF;
         LEAVE Loop2;

      END LOOP Loop2;

      SET @rowNumberL1 := @rowNumberL1 + 1;
      IF (@rowNumberL1 < 4) THEN 
         ITERATE Loop1;
      END IF;
      LEAVE Loop1;

   END LOOP Loop1;
END$$
DELIMITER ;

CALL MakeUCTable();

SELECT MAX(ROUND(ConditionalTable.Probability/UnconditionalTable.probability,12)) INTO @answer6 
   FROM ConditionalTable, UnconditionalTable WHERE AfterAction=Action;

SELECT @answer1 AS Answer1, @answer2 AS Answer2, @answer3 AS Answer3, @answer4 AS Answer4, @answer5 AS Answer5, @answer6 AS Answer6; 
