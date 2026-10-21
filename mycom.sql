
CREATE TABLE user_table (
                id_num     INTEGER PRIMARY KEY AUTOINCREMENT,  -- 관리번호
                userid     TEXT    NOT NULL UNIQUE,            -- 로그인 아이디
                username   TEXT    NOT NULL,                   -- 이름
                password   TEXT    NOT NULL,                   -- 해시된 비밀번호
                email      TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            );
CREATE TABLE "survey_table" (
	"id_num"	INTEGER NOT NULL,
	"user_id"	TEXT,
	"q1"	INTEGER,
	"q2"	INTEGER,
	"q3"	INTEGER,
	"q4"	INTEGER,
	"q5"	INTEGER,
	"q6"	INTEGER,
	"q7"	INTEGER,
	"q8"	INTEGER,
	"q9"	INTEGER,
	"q10"	INTEGER,
	"created_at"	TEXT,
	PRIMARY KEY("id_num" AUTOINCREMENT)
);
