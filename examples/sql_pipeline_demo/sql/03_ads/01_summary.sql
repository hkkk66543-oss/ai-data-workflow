CREATE TABLE `应用_类别汇总` (
  `类别` VARCHAR(10) PRIMARY KEY COMMENT '汇总类别',
  `记录数` BIGINT NOT NULL COMMENT '该类别明细行数',
  `数值合计` DECIMAL(14,2) NOT NULL COMMENT '该类别数值之和'
) ENGINE=InnoDB COMMENT='合成数据类别汇总';
INSERT INTO `应用_类别汇总`
SELECT `类别`, COUNT(*), SUM(`数值`) FROM `清洗_记录` GROUP BY `类别`;
