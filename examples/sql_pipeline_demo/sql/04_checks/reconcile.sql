SELECT (SELECT SUM(`数值`) FROM `清洗_记录`) - (SELECT SUM(`数值合计`) FROM `应用_类别汇总`) AS `差额`;
