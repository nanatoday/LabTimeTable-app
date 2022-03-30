Create DATABASE Labtimetable;
Use Labtimetable;

CREATE TABLE users(
lecId int PRIMARY KEY auto_increment,
firstName varchar(20) not null,
lastName varchar(20) not null,
email varchar(30) not null,
lecPassword varchar(80) not null,
verification varchar(5) not null default 'NO');

CREATE TABLE lab1(
slotId int PRIMARY KEY AUTO_INCREMENT,
slotTime varchar(15) null,
initials varchar(5) null,
courseCode varchar(20) null,
slotDay varchar(20) null,
);

CREATE TABLE lab2(
slotId int PRIMARY KEY AUTO_INCREMENT,
slotTime varchar(15) null,
initials varchar(5  ) null,
courseCode varchar(20) null,
slotDay varchar(20) null,
);

CREATE TABLE admin(
adminId int PRIMARY KEY AUTO_INCREMENT,
username varchar(30) not null,
email varchar(30) not null,
password varchar(80),
verification varchar(5) not null default 'NO');

