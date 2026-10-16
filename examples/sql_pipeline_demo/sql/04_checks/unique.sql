SELECT `记录编号` FROM `清洗_记录` GROUP BY `记录编号` HAVING COUNT(*) > 1;
