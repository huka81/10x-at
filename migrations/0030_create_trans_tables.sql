
CREATE TABLE trans.br_quotes (
	oid int4 NOT NULL,
	raw_ts int8 NOT NULL,
	day_nbr int4 NULL,
	ts_dt timestamp NULL,
	min numeric NULL,
	max numeric NULL,
	open numeric NULL,
	close numeric NULL,
	volume numeric NULL,
	amount numeric NULL,
	grain text NULL,
    ins_ts timestamp DEFAULT CURRENT_TIMESTAMP,
    upd_ts timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (oid, raw_ts)
);


CREATE TABLE trans.session_calendar (
    session_date date PRIMARY KEY,
    session_nbr int NOT NULL
);
