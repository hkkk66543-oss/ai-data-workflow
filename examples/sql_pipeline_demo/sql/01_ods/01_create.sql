-- 合成演示：明确类型与注释，不自动推断业务口径。
CREATE TABLE `原始_记录` (
  `记录编号` VARCHAR(10) PRIMARY KEY COMMENT '原始记录编号，保留前导零',
  `类别` VARCHAR(10) NOT NULL COMMENT '合成分类标签',
  `数值` DECIMAL(12,2) NOT NULL COMMENT '演示数值',
  `记录日期` DATE NOT NULL COMMENT '原始记录日期'
) ENGINE=InnoDB COMMENT='合成原始记录';
