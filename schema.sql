-- Table: userlog
CREATE TABLE `userlog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: molecules
CREATE TABLE `molecules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table: report
CREATE TABLE `report` (
  `product_name` varchar(40) NOT NULL,
  `yeild` float NOT NULL,
  `time` float NOT NULL,
  `emy` float NOT NULL,
  `ae` float NOT NULL,
  `aef` float NOT NULL,
  `ce` float NOT NULL,
  `rme` float NOT NULL,
  `oe` float NOT NULL,
  `pmi` float NOT NULL,
  `mi` float NOT NULL,
  `mp` float NOT NULL,
  `e_factor` float NOT NULL,
  `si` float NOT NULL,
  `wi` float NOT NULL,
  `ton` float NOT NULL,
  `tof` float NOT NULL,
  `user` varchar(40) NOT NULL,
  PRIMARY KEY (`product_name`,`yeild`,`time`,`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
