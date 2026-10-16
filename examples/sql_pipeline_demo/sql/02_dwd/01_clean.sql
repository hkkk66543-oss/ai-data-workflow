CREATE TABLE `维度_类别` (
  `类别` VARCHAR(10) PRIMARY KEY COMMENT '类别去重结果'
) ENGINE=InnoDB COMMENT='演示类别维度';
INSERT INTO `维度_类别` SELECT DISTINCT TRIM(`类别`) FROM `原始_记录`;
CREATE TABLE `清洗_记录` (
  `记录编号` VARCHAR(10) PRIMARY KEY COMMENT '来源原始记录编号',
  `类别` VARCHAR(10) NOT NULL COMMENT '原始类别去除首尾空格',
  `数值` DECIMAL(12,2) NOT NULL COMMENT '原始数值，未改动',
  `记录日期` DATE NOT NULL COMMENT '原始日期，未改动',
  CONSTRAINT `类别关联` FOREIGN KEY (`类别`) REFERENCES `维度_类别` (`类别`)
) ENGINE=InnoDB COMMENT='演示清洗明细';
INSERT INTO `清洗_记录`
SELECT `记录编号`, TRIM(`类别`), `数值`, `记录日期` FROM `原始_记录`;
