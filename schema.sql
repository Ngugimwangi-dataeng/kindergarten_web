--
-- PostgreSQL database dump
--

\restrict atEPP8jsImUMpKqgkECIcCqx8SLqxcLOY9w8dkgsHfRfDyanu2wPJs3MFaRB77m

-- Dumped from database version 18.6 (Debian 18.6-3)
-- Dumped by pg_dump version 18.6 (Debian 18.6-3)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attendance_handshakes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendance_handshakes (
    id integer NOT NULL,
    child_id integer,
    action_type character varying(20) NOT NULL,
    guardian_id integer,
    guardian_name_snapshot character varying(120),
    teacher_username character varying(80) NOT NULL,
    departure_notes text,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: attendance_handshakes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attendance_handshakes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attendance_handshakes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attendance_handshakes_id_seq OWNED BY public.attendance_handshakes.id;


--
-- Name: authorized_guardians; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.authorized_guardians (
    id integer NOT NULL,
    child_id integer,
    full_name character varying(120) NOT NULL,
    relationship character varying(50) NOT NULL,
    phone_number character varying(35) NOT NULL,
    email character varying(120) DEFAULT NULL::character varying,
    is_primary boolean DEFAULT false,
    id_verified boolean DEFAULT true,
    verification_pin character varying(6) DEFAULT NULL::character varying,
    government_id_type character varying(50) DEFAULT 'State Driver License'::character varying,
    photo_url text,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    access_type character varying(20) DEFAULT 'Permanent'::character varying,
    pickup_expires_at timestamp with time zone,
    pickup_used_at timestamp with time zone,
    authorized_by character varying(80),
    verification_attempts integer DEFAULT 0,
    national_id_number character varying(50)
);


--
-- Name: authorized_guardians_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.authorized_guardians_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: authorized_guardians_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.authorized_guardians_id_seq OWNED BY public.authorized_guardians.id;


--
-- Name: children; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.children (
    id integer NOT NULL,
    first_name character varying(80) NOT NULL,
    last_name character varying(80) NOT NULL,
    date_of_birth date,
    classroom_id integer,
    room_name character varying(50) DEFAULT 'Toddler Room B'::character varying,
    current_status character varying(40) DEFAULT 'Checked Out'::character varying,
    allergy_info text,
    dietary_restrictions text,
    emergency_notes text,
    parent_first_name character varying(80),
    parent_last_name character varying(80),
    parent_phone character varying(35) NOT NULL,
    parent_email character varying(120) DEFAULT NULL::character varying,
    preferred_channel character varying(20) DEFAULT 'Both'::character varying,
    last_status_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_action_by character varying(80) DEFAULT NULL::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: children_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.children_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: children_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.children_id_seq OWNED BY public.children.id;


--
-- Name: classrooms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classrooms (
    id integer NOT NULL,
    name character varying(80) NOT NULL,
    age_group character varying(60),
    target_ratio_child integer DEFAULT 4,
    max_capacity integer DEFAULT 15,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: classrooms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classrooms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: classrooms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classrooms_id_seq OWNED BY public.classrooms.id;


--
-- Name: daily_care_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.daily_care_logs (
    id integer NOT NULL,
    child_id integer,
    teacher_username character varying(80) NOT NULL,
    category character varying(30) NOT NULL,
    title character varying(120) NOT NULL,
    details text,
    metric_value character varying(60),
    logged_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    parent_notified boolean DEFAULT false,
    notification_channel character varying(20) DEFAULT 'Email'::character varying
);


--
-- Name: daily_care_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.daily_care_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: daily_care_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.daily_care_logs_id_seq OWNED BY public.daily_care_logs.id;


--
-- Name: message_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message_logs (
    id integer NOT NULL,
    child_id integer,
    recipient_phone character varying(35),
    recipient_email character varying(120),
    first_name character varying(80),
    last_name character varying(80),
    channel character varying(20) DEFAULT 'SMS'::character varying NOT NULL,
    direction character varying(20) DEFAULT 'outbound'::character varying NOT NULL,
    subject character varying(200) DEFAULT NULL::character varying,
    message_body text NOT NULL,
    delivery_status character varying(40) DEFAULT 'Delivered'::character varying,
    at_message_id character varying(100) DEFAULT NULL::character varying,
    received_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: message_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.message_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: message_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.message_logs_id_seq OWNED BY public.message_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(30) DEFAULT 'teacher'::character varying NOT NULL,
    full_name character varying(120),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attendance_handshakes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_handshakes ALTER COLUMN id SET DEFAULT nextval('public.attendance_handshakes_id_seq'::regclass);


--
-- Name: authorized_guardians id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_guardians ALTER COLUMN id SET DEFAULT nextval('public.authorized_guardians_id_seq'::regclass);


--
-- Name: children id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children ALTER COLUMN id SET DEFAULT nextval('public.children_id_seq'::regclass);


--
-- Name: classrooms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms ALTER COLUMN id SET DEFAULT nextval('public.classrooms_id_seq'::regclass);


--
-- Name: daily_care_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_care_logs ALTER COLUMN id SET DEFAULT nextval('public.daily_care_logs_id_seq'::regclass);


--
-- Name: message_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_logs ALTER COLUMN id SET DEFAULT nextval('public.message_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: attendance_handshakes attendance_handshakes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_handshakes
    ADD CONSTRAINT attendance_handshakes_pkey PRIMARY KEY (id);


--
-- Name: authorized_guardians authorized_guardians_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_guardians
    ADD CONSTRAINT authorized_guardians_pkey PRIMARY KEY (id);


--
-- Name: children children_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_pkey PRIMARY KEY (id);


--
-- Name: classrooms classrooms_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_name_key UNIQUE (name);


--
-- Name: classrooms classrooms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_pkey PRIMARY KEY (id);


--
-- Name: daily_care_logs daily_care_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_care_logs
    ADD CONSTRAINT daily_care_logs_pkey PRIMARY KEY (id);


--
-- Name: message_logs message_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_logs
    ADD CONSTRAINT message_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: attendance_handshakes attendance_handshakes_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_handshakes
    ADD CONSTRAINT attendance_handshakes_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE CASCADE;


--
-- Name: attendance_handshakes attendance_handshakes_guardian_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_handshakes
    ADD CONSTRAINT attendance_handshakes_guardian_id_fkey FOREIGN KEY (guardian_id) REFERENCES public.authorized_guardians(id) ON DELETE SET NULL;


--
-- Name: authorized_guardians authorized_guardians_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_guardians
    ADD CONSTRAINT authorized_guardians_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE CASCADE;


--
-- Name: children children_classroom_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_classroom_id_fkey FOREIGN KEY (classroom_id) REFERENCES public.classrooms(id) ON DELETE SET NULL;


--
-- Name: daily_care_logs daily_care_logs_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_care_logs
    ADD CONSTRAINT daily_care_logs_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE CASCADE;


--
-- Name: message_logs message_logs_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_logs
    ADD CONSTRAINT message_logs_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict atEPP8jsImUMpKqgkECIcCqx8SLqxcLOY9w8dkgsHfRfDyanu2wPJs3MFaRB77m

