--
-- PostgreSQL database dump
--

\restrict vodruMwB4ClBKEPTtcNLbuRZddmw8937T8z6ZpB1gc0Z01keMMm3iS5vRJDNAMM

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

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, password_hash, role, full_name, created_at) FROM stdin;
1	admin	scrypt:32768:8:1$COr1z8Ts0MkPsAWZ$743f30cce42639782a1270237f17384d09e2ef4c8ce090ac4721264c3432be8cdce83d9b9de9cf4419cc0467c62fbfc96e1c3d04f2c2107edb821b32d2e396bb	manager	Daycare Administrator	2026-10-31 21:42:35.351492+03
2	Alex	scrypt:32768:8:1$T2w0HZGqBWI6Nedn$cf43fe562c37bbb5311dd963dd97dd750e354ed3188e319125383fcd2aeb36c07280ff6fda6251fbfd20f67a90f522a48a7f614d55009b329d8a358bff3f9e39	teacher	\N	2026-10-31 22:25:35.05191+03
3	jerry	scrypt:32768:8:1$XpEfyx2SADiisbcg$1fa641eb1419d118be451a0f8972b836e3928db2b454fddf16e23762732377cfad6c50ca506875e4b8d075ecec570ff312dda01968910d2440ff5fd31bbbf876	teacher	\N	2026-11-01 00:03:23.317851+03
\.


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- PostgreSQL database dump complete
--

\unrestrict vodruMwB4ClBKEPTtcNLbuRZddmw8937T8z6ZpB1gc0Z01keMMm3iS5vRJDNAMM

