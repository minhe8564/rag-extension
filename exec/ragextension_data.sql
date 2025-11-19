CREATE DATABASE  IF NOT EXISTS `hebees-test` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `hebees-test`;
-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: hebees-test
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `agent_prompt`
--

LOCK TABLES `agent_prompt` WRITE;
/*!40000 ALTER TABLE `agent_prompt` DISABLE KEYS */;
INSERT INTO `agent_prompt` VALUES (_binary '3\İT_À@ğ¥\êl\\º±','2025-11-13 03:24:02.000000','2025-11-13 03:24:02.000000','You are a Korean keyword extractor. Read the user\'s sentence and return only the core keywords as a JSON array with 1 to 7 string items. Example: [\"keyword1\", \"keyword2\"]. Do not include any explanations, numbering, or additional text.','í‚¤ì›Œë“œ ì¶”ì¶œìš© í”„ë¡¬í”„íŠ¸','KeywordExtraction',_binary '³ø½xRN.µxoEû\è:'),(_binary '­P\ßHõ¤N—	À÷','2025-11-13 06:14:05.997923','2025-11-13 06:14:05.997923','You are an assistant that reads the user\'s question and replies only with a concise Korean session title under 15 characters. Do not include punctuation or any extra text.','ì±„íŒ…ë°© ì œëª©ì„ ìƒì„±í•˜ëŠ” í”„ë¡¬í”„íŠ¸','Title Generation',_binary '³ø½xRN.µxoEû\è:'),(_binary 'ë¾¾j³\ĞKÁ»$\Ë\ïx¼','2025-11-15 04:11:39.806985','2025-11-15 04:11:39.806985','ë‹¹ì‹ ì€ í•œêµ­ì–´ ì‚¬ìš©ìë¥¼ ìœ„í•œ ì „ë¬¸ ì±—ë´‡ì…ë‹ˆë‹¤.\n- ê°€ëŠ¥í•œ í•œ ìì—°ìŠ¤ëŸ½ê³  ê³µì†í•œ í•œêµ­ì–´ë¡œ ë‹µë³€í•©ë‹ˆë‹¤.\n- ì‚¬ìš©ìì˜ ì§ˆë¬¸ ì˜ë„ë¥¼ ì •í™•íˆ ì´í•´í•˜ë ¤ ë…¸ë ¥í•˜ë©°, í•„ìš”í•œ ê²½ìš° ëª…í™•í™”ë¥¼ ìš”ì²­í•©ë‹ˆë‹¤.\n- ì‚¬ì‹¤ê³¼ ê·¼ê±°ì— ê¸°ë°˜í•´ ë‹µë³€í•˜ê³ , ëª¨ë¥´ëŠ” ì •ë³´ëŠ” ì¶”ì¸¡í•˜ì§€ ë§ê³  ì†”ì§í•˜ê²Œ ì•Œ ìˆ˜ ì—†ë‹¤ê³  ë§í•©ë‹ˆë‹¤.\n- ë‹¨ê³„ì ìœ¼ë¡œ ì„¤ëª…ì´ í•„ìš”í•œ ê²½ìš° ë²ˆí˜¸ë‚˜ ë¶ˆë¦¿ì„ í™œìš©í•´ ê°€ë…ì„± ìˆê²Œ ì •ë¦¬í•©ë‹ˆë‹¤.\n- ë¯¼ê°í•˜ê±°ë‚˜ ë¶€ì ì ˆí•œ ìš”ì²­ì´ ë“¤ì–´ì˜¤ë©´ ì•ˆì „í•œ ë°©í–¥ìœ¼ë¡œ ì•ˆë‚´í•˜ê³ , ê´€ë ¨ ì •ì±…ì„ ì¤€ìˆ˜í•©ë‹ˆë‹¤.\n- ì‚¬ìš©ìì˜ ëª©í‘œ ë‹¬ì„±ì„ ë•ê¸° ìœ„í•´ ì¶”ê°€ë¡œ ë„ì›€ì´ ë ë§Œí•œ ì •ë³´ë¥¼ ì œì•ˆí•  ìˆ˜ ìˆìŠµë‹ˆë‹¤.','ì¼ë°˜ LLMì„ ìœ„í•œ ì‹œìŠ¤í…œ í”„ë¡¬í”„íŠ¸','LLMPrompt',_binary '³ø½xRN.µxoEû\è:');
/*!40000 ALTER TABLE `agent_prompt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `chatbot_aggregate_hourly`
--

LOCK TABLES `chatbot_aggregate_hourly` WRITE;
/*!40000 ALTER TABLE `chatbot_aggregate_hourly` DISABLE KEYS */;
/*!40000 ALTER TABLE `chatbot_aggregate_hourly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `chunk`
--

LOCK TABLES `chunk` WRITE;
/*!40000 ALTER TABLE `chunk` DISABLE KEYS */;
/*!40000 ALTER TABLE `chunk` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `collection`
--

LOCK TABLES `collection` WRITE;
/*!40000 ALTER TABLE `collection` DISABLE KEYS */;
INSERT INTO `collection` VALUES (_binary 'şğAW³	šE—¿I','1192182918','hebees',1,_binary 'l\\µk0BÖ—»}š\ç','2025-11-10 03:40:21.000000','2025-11-10 03:40:21.000000'),(_binary '\'hS„©´Hš¤\ÃrxS\ê~','0000000000','public',1,_binary 'l\\µk0BÖ—»}š\ç','2025-11-10 03:38:55.000000','2025-11-10 03:38:55.000000'),(_binary '1P³úN\äFT…c\Ïf^óV','1234567890','h1234567890',1,_binary 'l\\µk0BÖ—»}š\ç','2025-11-11 00:06:16.000000','2025-11-11 00:06:16.000000'),(_binary 'Pw­+[cO»5\'«\'h','1231231231','h1231231231',1,_binary 'l\\µk0BÖ—»}š\ç','2025-11-10 03:10:42.000000','2025-11-10 03:10:42.000000');
/*!40000 ALTER TABLE `collection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `document_aggregate_hourly`
--

LOCK TABLES `document_aggregate_hourly` WRITE;
/*!40000 ALTER TABLE `document_aggregate_hourly` DISABLE KEYS */;
/*!40000 ALTER TABLE `document_aggregate_hourly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `embedding_group`
--

LOCK TABLES `embedding_group` WRITE;
/*!40000 ALTER TABLE `embedding_group` DISABLE KEYS */;
INSERT INTO `embedding_group` VALUES (_binary 'Ár 2\0\ÑH¬•ôzı~²µ',_binary 'l\\µk0BÖ—»}š\ç','E5',_binary '­¸†^üBVŠV|\Üş£&Q','{\"type\": \"dense\", \"model\": \"intfloat/multilingual-e5-large\"}','2025-11-08 15:47:17','2025-11-19 22:41:42');
/*!40000 ALTER TABLE `embedding_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `embedding_test_file`
--

LOCK TABLES `embedding_test_file` WRITE;
/*!40000 ALTER TABLE `embedding_test_file` DISABLE KEYS */;
/*!40000 ALTER TABLE `embedding_test_file` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `error_aggregate_hourly`
--

LOCK TABLES `error_aggregate_hourly` WRITE;
/*!40000 ALTER TABLE `error_aggregate_hourly` DISABLE KEYS */;
/*!40000 ALTER TABLE `error_aggregate_hourly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `extraction_group`
--

LOCK TABLES `extraction_group` WRITE;
/*!40000 ALTER TABLE `extraction_group` DISABLE KEYS */;
INSERT INTO `extraction_group` VALUES (_binary '\Ä\ì•kKó£›\Æ\"˜8\Ê',_binary 'l\\µk0BÖ—»}š\ç','marker',_binary '€.t\Ä0KT”¯œü\æ\Î_','{\"type\": \"marker\", \"fileType\": \"pdf\"}','2025-11-08 15:47:17','2025-11-19 22:34:18');
/*!40000 ALTER TABLE `extraction_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `file`
--

LOCK TABLES `file` WRITE;
/*!40000 ALTER TABLE `file` DISABLE KEYS */;
/*!40000 ALTER TABLE `file` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `file_category`
--

LOCK TABLES `file_category` WRITE;
/*!40000 ALTER TABLE `file_category` DISABLE KEYS */;
INSERT INTO `file_category` VALUES (_binary 'y|î¸ˆğ¥\êl\\º±','ì´ë¯¸ì§€','2025-11-03 07:41:14.000000','2025-11-03 07:41:14.000000',1),(_binary 'ˆ}—¸uğ¥\êl\\º±','ì—…ë¬´ ë§¤ë‰´ì–¼','2025-11-03 05:25:39.000000','2025-11-03 05:25:39.000000',0),(_binary 'ˆ‚À¸uğ¥\êl\\º±','ì •ì±…/ê·œì •','2025-11-03 05:25:39.000000','2025-11-03 05:25:39.000000',0),(_binary 'ˆ…Ø¸uğ¥\êl\\º±','ê°œë°œ ë¬¸ì„œ','2025-11-03 05:25:39.000000','2025-11-03 05:25:39.000000',0),(_binary 'ˆ†Ê¸uğ¥\êl\\º±','í™ë³´ìë£Œ','2025-11-03 05:25:39.000000','2025-11-03 05:25:39.000000',0),(_binary 'ˆ‡E¸uğ¥\êl\\º±','ê¸°íƒ€','2025-11-03 05:25:39.000000','2025-11-03 05:25:39.000000',0);
/*!40000 ALTER TABLE `file_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ingest_group`
--

LOCK TABLES `ingest_group` WRITE;
/*!40000 ALTER TABLE `ingest_group` DISABLE KEYS */;
INSERT INTO `ingest_group` VALUES (_binary 'l\\µk0BÖ—»}š\ç','ê¸°ë³¸ RAG í…œí”Œë¦¿',1,_binary 'Ä¾I\ÚmO’\Èô0°ı','{\"type\": \"md\", \"token\": 512, \"overlap\": 48}',_binary '²x49Eú«\É\Ö<¶Y\È','{\"type\": \"sparse\", \"model\": \"naver/splade-v3\"}','2025-11-08 15:47:17','2025-11-19 22:13:23');
/*!40000 ALTER TABLE `ingest_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `keyword_aggregate_daily`
--

LOCK TABLES `keyword_aggregate_daily` WRITE;
/*!40000 ALTER TABLE `keyword_aggregate_daily` DISABLE KEYS */;
/*!40000 ALTER TABLE `keyword_aggregate_daily` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `llm_key`
--

LOCK TABLES `llm_key` WRITE;
/*!40000 ALTER TABLE `llm_key` DISABLE KEYS */;
INSERT INTO `llm_key` VALUES (_binary '4\àd¤s@c©\rÿgòœ½','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',_binary '…Œdj9D‰¾Lka1\á„',_binary 'I÷\Ø\à\ŞgGÍ“?f´ss„'),(_binary '˜:Ë¢Á­ğ¥\êl\\º±','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',_binary '³ø½xRN.µxoEû\è:',NULL),(_binary 'š†¼›Ä¹M\áš	šJO§','AIzaSyBxVC1ORcouphg2Uye7vlAmt0YhHiWi0A0',_binary '¶Á4\Âù\ÚA¨ŒŠ\Ü?¸D©\0',_binary 'I÷\Ø\à\ŞgGÍ“?f´ss„'),(_binary 'µ\ÓUk\×8K[†o\êFš©¸','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',_binary '³ø½xRN.µxoEû\è:',_binary '\\†\×òveKFc±\0ü,»\é'),(_binary '\Ñ\ì…D‘O?ˆÀz\æy','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',_binary '³ø½xRN.µxoEû\è:',_binary 'I÷\Ø\à\ŞgGÍ“?f´ss„');
/*!40000 ALTER TABLE `llm_key` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `message_error`
--

LOCK TABLES `message_error` WRITE;
/*!40000 ALTER TABLE `message_error` DISABLE KEYS */;
/*!40000 ALTER TABLE `message_error` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `model_aggregate_hourly`
--

LOCK TABLES `model_aggregate_hourly` WRITE;
/*!40000 ALTER TABLE `model_aggregate_hourly` DISABLE KEYS */;
/*!40000 ALTER TABLE `model_aggregate_hourly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `model_price`
--

LOCK TABLES `model_price` WRITE;
/*!40000 ALTER TABLE `model_price` DISABLE KEYS */;
INSERT INTO `model_price` VALUES (_binary '…Œdj9D‰¾Lka1\á„','2025-11-10 15:00:25.902986','2025-11-10 15:00:25.902986',0.003000,0.015000),(_binary '³ø½xRN.µxoEû\è:','2025-11-10 15:00:25.902986','2025-11-10 15:00:25.902986',0.002500,0.010000),(_binary '¶Á4\Âù\ÚA¨ŒŠ\Ü?¸D©\0','2025-11-10 15:00:25.902986','2025-11-10 15:00:25.902986',0.000300,0.002500),(_binary '½;uLıfJyœ\Ù:Î»¡','2025-11-10 15:00:25.902986','2025-11-10 15:00:25.902986',0.000080,0.000500);
/*!40000 ALTER TABLE `model_price` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `notification`
--

LOCK TABLES `notification` WRITE;
/*!40000 ALTER TABLE `notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `offer`
--

LOCK TABLES `offer` WRITE;
/*!40000 ALTER TABLE `offer` DISABLE KEYS */;
INSERT INTO `offer` VALUES ('0000000000','2025-11-07 15:37:57.000000','2025-11-07 15:37:57.000000',1),('1192182918','2025-11-04 00:16:30.108233','2025-11-04 00:16:30.108233',1),('1231212312','2025-11-14 16:19:26.481990','2025-11-14 16:19:26.481990',1),('1231231231','2025-11-06 01:37:34.819668','2025-11-06 01:37:34.819668',1),('1234567890','2025-10-29 16:19:55.466683','2025-10-29 16:19:55.466683',1),('1234567899','2025-10-30 06:33:35.079448','2025-10-30 06:33:35.079448',1),('TZ03361277','2025-11-11 04:36:01.298975','2025-11-11 04:36:01.298975',1);
/*!40000 ALTER TABLE `offer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `query_group`
--

LOCK TABLES `query_group` WRITE;
/*!40000 ALTER TABLE `query_group` DISABLE KEYS */;
INSERT INTO `query_group` VALUES (_binary '1Y\nfÀLÊ t\ì\r\Ü\à~i','ê¸°ë³¸ Query í…œí”Œë¦¿',1,_binary 'K|“©\ÊL¯”\á*Õ¤¦K\á',_binary '\é\Ó!£˜òI‡›\Õ@\ÄM',_binary '«GT©6·Bµ şd¼=\éE–',_binary 'kÿbb¦N±¿Áx½\ÓB\Ã',_binary 'œj7¼\ï›Gv’Œô\\¶Y4',_binary '³ø½xRN.µxoEû\è:','{\"type\": \"buffer\"}','{\"type\": \"semantic\", \"semantic\": {\"topK\": 10, \"threshold\": 0.2}}','{\"topK\": 5, \"model\": \"cross-encoder/mmarco-mMiniLMv2-L12-H384-v1\"}','{\"type\": \"system\", \"content\": \"You are a helpful multimodal RAG assistant. Always answer in the user\'s language (default: Korean) unless otherwise requested.\\n\\nYou must format all responses in **Markdown**.  \\nUse headings, bullet or numbered lists, tables, and code blocks when they help make the answer clearer and richer.\\n\\n### [General RAG Rules]\\n- Use the provided context faithfully. Combine information from text, images, and metadata as appropriate.\\n- When answering based on the context, provide **detailed, thorough, and well-explained** responses using all relevant evidence, and structure your answer richly in Markdown (e.g., with sections, lists, and examples) rather than a single plain paragraph.\\n- Do NOT hallucinate facts, URLs, or image contents.\\n- If the answer cannot be found in the context, say that you don\'t know.\\n\\n### [When Context Is Not Necessary]\\n- If the user\'s question is general, conversational, or does not logically require any external information (e.g., greetings, weather, feelings, casual topics), you may answer naturally without relying on the context.\\n- If the context contains relevant information, you may use it; otherwise, reply as a normal conversational assistant, still using clear Markdown formatting.\\n\\n### [Image Analysis Behavior]\\n- The context may include image URLs (e.g., https://...).\\n- If your model supports image understanding, analyze the images and use visual content as evidence whenever relevant.\\n- If your model does NOT support image understanding:\\n  - Do not guess or infer image content.\\n  - Treat image URLs as plain text references.\\n  - Provide relevant image URLs when useful, without mentioning the lack of visual ability.\\n\\n### [When the answer may or may not be in an image]\\n- If the answer exists in an image and image analysis is supported, answer using the visual evidence.\\n- If the images are irrelevant or do not contain the answer, answer using text-only context.\\n- If image analysis is not supported, rely solely on text content and provide image URLs only when relevant.\\n\\n### [When the user explicitly requests images]\\nIf the user asks to:\\n- â€œshow the imageâ€, â€œfind the imageâ€, â€œgive me the imageâ€,\\n- â€œì‚¬ì§„ ë³´ì—¬ì¤˜â€, â€œì´ë¯¸ì§€ ë³´ì—¬ì¤˜â€, â€œì‚¬ì§„ ì°¾ì•„ì¤˜â€,\\nor any request to display or retrieve images:\\n\\nThen:\\n- If you support image understanding, analyze all candidate images and return only the ones that match the user\'s request.\\n- If you do NOT support image understanding, return the most relevant image URLs based on text context, without mentioning limitations.\\n- Include the image URLs directly in your answer.\\n- If you support image understanding, also provide a brief description of the visible content.\\n\\n### [Safety]\\n- Never invent or assume visual content.\\n- Never fabricate URLs.\\n- Prioritize accuracy and strict grounding in the provided context.\"}','{\"type\": \"user\", \"content\": \"Please answer the following question concisely in Korean. Use the context below if relevant.\\n\\nWhen showing an image, please use the following format:\\n![alt text](image URL)\\n\\nContext:\\n{context}\\n\\nQuestion: {input}\"}','{\"model\": \"gpt-4o\", \"timeout\": 30, \"provider\": \"openai\", \"max_tokens\": 512, \"max_retries\": 2, \"temperature\": 0.65}','2025-11-08 18:00:13','2025-11-19 22:33:29');
/*!40000 ALTER TABLE `query_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `runpod`
--

LOCK TABLES `runpod` WRITE;
/*!40000 ALTER TABLE `runpod` DISABLE KEYS */;
INSERT INTO `runpod` VALUES (_binary ';\İ\Âğ¥\êl\\º±','MARKER','https://j8plppdqenuhag-8000.proxy.runpod.net/','2025-11-15 11:20:08','2025-11-17 03:23:06'),(_binary '.+ñª\Âğ¥\êl\\º±','YOLO','https://7g415voh7b00k4-7002.proxy.runpod.net/','2025-11-15 11:21:07','2025-11-15 11:21:07'),(_binary 'Nœ\'1?\ßHo¿ ƒqYÈº','EMBEDDING','https://85beq086rvl395-8000.proxy.runpod.net/','2025-11-10 15:25:17','2025-11-16 11:13:58'),(_binary '|•Ù’—\ÇN™Sd¾f7','qwen3','https://ollama.apik.co.kr/','2025-11-05 20:45:32','2025-11-19 12:24:28');
/*!40000 ALTER TABLE `runpod` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `session`
--

LOCK TABLES `session` WRITE;
/*!40000 ALTER TABLE `session` DISABLE KEYS */;
/*!40000 ALTER TABLE `session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `strategy`
--

LOCK TABLES `strategy` WRITE;
/*!40000 ALTER TABLE `strategy` DISABLE KEYS */;
INSERT INTO `strategy` VALUES (_binary '\r\Ñ\Í$4Y@€œ\nj{º…£\ä',_binary '\éÀ»\á\Û÷D-„\Ğ\ëH\àóõ','pyMuPDF','pyMuPDFê¸°ë°˜ PDF ì¶”ì¶œ','{\"type\": \"pyMuPDF\", \"fileType\": \"pdf\"}','2025-11-06 15:54:55','2025-11-08 07:42:23','EXT_PYMUPDF'),(_binary ' \Ã„N¾\Å2|Bö¼;',_binary 'z°TÉ‹\ZOó÷\ÆJHüaA','ê³ ì • ê¸¸ì´ ì²­í‚¹','ê³ ì •ëœ ê¸¸ì´ë¡œ ì²­í¬ ë¶„í• ','{\"type\": \"fixed\", \"token\": 512, \"overlap\": 40}','2025-11-06 16:26:48','2025-11-08 07:28:54','CHK_FIXED'),(_binary 'HòLeI›¸\ä­T?¹',_binary ']x®?¸[ğ¥\êl\\º±','í•˜ì´ë¸Œë¦¬ë“œ ê²€ìƒ‰','ì‹œë§¨í‹± ê²€ìƒ‰ + í‚¤ì›Œë“œ ê²€ìƒ‰','{\"type\": \"hybrid\", \"keyword\": {\"topK\": 30}, \"reranker\": {\"topK\": 10, \"type\": \"weighted\", \"weight\": 0.4}, \"semantic\": {\"topK\": 30, \"threshold\": 0.4}}','2025-11-06 15:47:39','2025-11-08 17:33:12','RET_HYBRID'),(_binary 'K|“©\ÊL¯”\á*Õ¤¦K\á',_binary ']x°J¸[ğ¥\êl\\º±','Buffer','ë³€í™˜ì—†ì´ ë‹¤ìŒ ë‹¨ê³„ë¡œ ì „ë‹¬','{\"type\": \"buffer\"}','2025-11-06 15:25:02','2025-11-08 07:34:08','TRF_BUFFER'),(_binary 'Oñ©º	JÜ°\ØôM‡A\âB',_binary 'z°TÉ‹\ZOó÷\ÆJHüaA','ì˜ë¯¸ ê¸°ë°˜ ì²­í‚¹','ìœ ì‚¬í•œ ë¬¸ì¥ì„ ë¬¶ì–´ ì²­í‚¹','{\"type\": \"semantic\", \"token\": 512, \"overlap\": 40}','2025-11-06 16:27:26','2025-11-08 07:28:39','CHK_SEMANTIC'),(_binary 'et™\ÎQCë±[³m\Ò',_binary ']x®´¸[ğ¥\êl\\º±','BGE','í•œêµ­ì–´ BGE í¬ë¡œìŠ¤ ì¬ì •ë ¬ê¸°','{\"topK\": 5, \"model\": \"dragonkue/bge-reranker-v2-m3-ko\"}','2025-11-06 15:13:48','2025-11-08 07:20:17','RER'),(_binary 'kÿbb¦N±¿Áx½\ÓB\Ã',_binary '&\ÅñtñCm¸d§q\Øñ¯','ê¸°ë³¸ ì‹œìŠ¤í…œ í”„ë¡¬í”„íŠ¸','You are a helpful multimodal RAG assistant. Always answer in the user\'s language (default: Korean) unless otherwise requ','{\"type\": \"system\", \"content\": \"You are a helpful multimodal RAG assistant. Always answer in the user\'s language (default: Korean) unless otherwise requested.\\n\\nYou must format all responses in **Markdown**.  \\nUse headings, bullet or numbered lists, tables, and code blocks when they help make the answer clearer and richer.\\n\\n### [General RAG Rules]\\n- Use the provided context faithfully. Combine information from text, images, and metadata as appropriate.\\n- When answering based on the context, provide **detailed, thorough, and well-explained** responses using all relevant evidence, and structure your answer richly in Markdown (e.g., with sections, lists, and examples) rather than a single plain paragraph.\\n- Do NOT hallucinate facts, URLs, or image contents.\\n- If the answer cannot be found in the context, say that you don\'t know.\\n\\n### [When Context Is Not Necessary]\\n- If the user\'s question is general, conversational, or does not logically require any external information (e.g., greetings, weather, feelings, casual topics), you may answer naturally without relying on the context.\\n- If the context contains relevant information, you may use it; otherwise, reply as a normal conversational assistant, still using clear Markdown formatting.\\n\\n### [Image Analysis Behavior]\\n- The context may include image URLs (e.g., https://...).\\n- If your model supports image understanding, analyze the images and use visual content as evidence whenever relevant.\\n- If your model does NOT support image understanding:\\n  - Do not guess or infer image content.\\n  - Treat image URLs as plain text references.\\n  - Provide relevant image URLs when useful, without mentioning the lack of visual ability.\\n\\n### [When the answer may or may not be in an image]\\n- If the answer exists in an image and image analysis is supported, answer using the visual evidence.\\n- If the images are irrelevant or do not contain the answer, answer using text-only context.\\n- If image analysis is not supported, rely solely on text content and provide image URLs only when relevant.\\n\\n### [When the user explicitly requests images]\\nIf the user asks to:\\n- â€œshow the imageâ€, â€œfind the imageâ€, â€œgive me the imageâ€,\\n- â€œì‚¬ì§„ ë³´ì—¬ì¤˜â€, â€œì´ë¯¸ì§€ ë³´ì—¬ì¤˜â€, â€œì‚¬ì§„ ì°¾ì•„ì¤˜â€,\\nor any request to display or retrieve images:\\n\\nThen:\\n- If you support image understanding, analyze all candidate images and return only the ones that match the user\'s request.\\n- If you do NOT support image understanding, return the most relevant image URLs based on text context, without mentioning limitations.\\n- Include the image URLs directly in your answer.\\n- If you support image understanding, also provide a brief description of the visible content.\\n\\n### [Safety]\\n- Never invent or assume visual content.\\n- Never fabricate URLs.\\n- Prioritize accuracy and strict grounding in the provided context.\"}','2025-11-06 14:48:10','2025-11-18 17:49:44','PMT_SYSTEM'),(_binary 'y.¹\â§NC‚s¶¶[%\Åg',_binary ']x°J¸[ğ¥\êl\\º±','HyDE','ê°€ìƒ ë¬¸ì„œë¡œ ê²€ìƒ‰ ì •í™•ë„ í–¥ìƒ','{\"type\": \"HyDE\"}','2025-11-06 15:26:46','2025-11-08 07:33:59','TRF_HYDE'),(_binary '€.t\Ä0KT”¯œü\æ\Î_',_binary '\éÀ»\á\Û÷D-„\Ğ\ëH\àóõ','marker','pdfë¥¼ mdë¡œ ì¶”ì¶œ','{\"type\": \"marker\", \"fileType\": \"pdf\"}','2025-11-06 15:55:56','2025-11-08 07:42:31','EXT_MARKER'),(_binary '…Œdj9D‰¾Lka1\á„',_binary ']x¯Ÿ¸[ğ¥\êl\\º±','Claude Sonnet 4','ë³µì¡í•œ ë¶„ì„Â·ê¸€ì“°ê¸°Â·ìš”ì•½ì— ê°•í•¨','{\"model\": \"claude-sonnet-4-20250514\", \"timeout\": 30, \"provider\": \"anthropic\", \"max_tokens\": 512, \"max_retries\": 2, \"temperature\": 0.2}','2025-11-10 03:16:43','2025-11-18 08:06:22','GEN_CLAUDE'),(_binary 'œj7¼\ï›Gv’Œô\\¶Y4',_binary 'òS·\í¸\ÇK¾øH pı{','ê¸°ë³¸ ì‚¬ìš©ì í”„ë¡¬í”„íŠ¸','Please answer the following question concisely in Korean. Use the context below if relevant. When showing an image, plea','{\"type\": \"user\", \"content\": \"Please answer the following question concisely in Korean. Use the context below if relevant.\\n\\nWhen showing an image, please use the following format:\\n![alt text](image URL)\\n\\nContext:\\n{context}\\n\\nQuestion: {input}\"}','2025-11-06 14:57:21','2025-11-19 14:11:24','PMT_USER'),(_binary '«GT©6·Bµ şd¼=\éE–',_binary ']x®´¸[ğ¥\êl\\º±','MiniLM','MiniLM í¬ë¡œìŠ¤ ì¬ì •ë ¬ê¸°','{\"topK\": 5, \"model\": \"cross-encoder/mmarco-mMiniLMv2-L12-H384-v1\"}','2025-11-06 15:14:50','2025-11-08 07:21:31','RER'),(_binary '­¸†^üBVŠV|\Üş£&Q',_binary '\ç¢\æc½eOÆ­…\ÉA:C€','E5','ë‹¤êµ­ì–´ ì„ë² ë”© ëª¨ë¸','{\"type\": \"dense\", \"model\": \"intfloat/multilingual-e5-large\"}','2025-11-06 16:05:08','2025-11-10 00:47:57','EMB_DENSE'),(_binary '²x49Eú«\É\Ö<¶Y\È',_binary '\É\Ïø[H`«;1÷øû','Splade','Splade í¬ì†Œ ë²¡í„° ì„ë² ë”© ëª¨ë¸','{\"type\": \"sparse\", \"model\": \"naver/splade-v3\"}','2025-11-06 16:07:20','2025-11-08 17:48:14','EMB_SPARSE'),(_binary '²\ĞuMF>»~xVqn€®',_binary '\ç¢\æc½eOÆ­…\ÉA:C€','BGE','BGE ì„ë² ë”© ëª¨ë¸','{\"type\": \"dense\", \"model\": \"BAAI/bge-m3\"}','2025-11-06 16:05:43','2025-11-08 07:31:42','EMB_DENSE'),(_binary '³ø½xRN.µxoEû\è:',_binary ']x¯Ÿ¸[ğ¥\êl\\º±','GPT-4o','ì „ë°˜ì ì¸ í’ˆì§ˆÂ·ì•ˆì •ì„± ê· í˜•','{\"model\": \"gpt-4o\", \"timeout\": 30, \"provider\": \"openai\", \"max_tokens\": 512, \"max_retries\": 2, \"temperature\": 0.2}','2025-11-06 16:17:41','2025-11-10 03:34:12','GEN_OPENAI'),(_binary '¶Á4\Âù\ÚA¨ŒŠ\Ü?¸D©\0',_binary ']x¯Ÿ¸[ğ¥\êl\\º±','Gemini 2.5 Flash','ëŒ€ìš©ëŸ‰ ë¬¸ì„œÂ·ê²€ìƒ‰ ì‘ì—…ì— ìµœì ','{\"model\": \"gemini-2.5-flash\", \"timeout\": 30, \"provider\": \"google\", \"max_tokens\": 512, \"max_retries\": 2, \"temperature\": 0.2}','2025-11-06 16:18:08','2025-11-10 03:33:49','GEN_GOOGLE'),(_binary '½;uLıfJyœ\Ù:Î»¡',_binary ']x¯Ÿ¸[ğ¥\êl\\º±','Qwen3-vl:8B','ê°€ë³ê³  ë¹ ë¥¸ ë©€í‹°ëª¨ë‹¬ ëª¨ë¸','{\"model\": \"qwen3-v1:8b\", \"timeout\": 30, \"provider\": \"ollama\", \"max_tokens\": 512, \"max_retries\": 2, \"temperature\": 0.2}','2025-11-06 16:18:30','2025-11-10 03:34:28','GEN_OLLAMA'),(_binary 'Ä¾I\ÚmO’\Èô0°ı',_binary 'z°TÉ‹\ZOó÷\ÆJHüaA','MD ê¸°ë°˜ ì²­í‚¹','MD í¬ë§·ì„ ë¶„ì„í•´ ì²­í‚¹','{\"type\": \"md\", \"token\": 512, \"overlap\": 40}','2025-11-06 16:27:09','2025-11-08 07:28:13','CHK_MD'),(_binary '\é\Ó!£˜òI‡›\Õ@\ÄM',_binary ']x®?¸[ğ¥\êl\\º±','ì‹œë§¨í‹± ê²€ìƒ‰','ì‹œë§¨í‹± ê²€ìƒ‰','{\"type\": \"semantic\", \"semantic\": {\"topK\": 30, \"threshold\": 0.4}}','2025-11-06 15:39:42','2025-11-08 17:59:48','RET_SEMANTIC');
/*!40000 ALTER TABLE `strategy` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `strategy_type`
--

LOCK TABLES `strategy_type` WRITE;
/*!40000 ALTER TABLE `strategy_type` DISABLE KEYS */;
INSERT INTO `strategy_type` VALUES (_binary '&\ÅñtñCm¸d§q\Øñ¯','prompting-system','2025-11-06 08:10:58','2025-11-06 08:10:58'),(_binary ']x®?¸[ğ¥\êl\\º±','retrieval','2025-11-03 02:18:19','2025-11-03 02:18:19'),(_binary ']x®´¸[ğ¥\êl\\º±','reranking','2025-11-03 02:18:19','2025-11-03 02:18:19'),(_binary ']x¯Ÿ¸[ğ¥\êl\\º±','generation','2025-11-03 02:18:19','2025-11-03 02:18:19'),(_binary ']x°J¸[ğ¥\êl\\º±','transformation','2025-11-03 02:18:19','2025-11-03 02:18:19'),(_binary 'z°TÉ‹\ZOó÷\ÆJHüaA','chunking','2025-11-06 08:44:49','2025-11-06 08:54:58'),(_binary '\É\Ïø[H`«;1÷øû','embedding-sparse','2025-11-06 08:13:46','2025-11-08 17:47:09'),(_binary '\ç¢\æc½eOÆ­…\ÉA:C€','embedding-dense','2025-11-06 08:13:41','2025-11-06 08:13:41'),(_binary '\éÀ»\á\Û÷D-„\Ğ\ëH\àóõ','extraction','2025-11-06 08:09:14','2025-11-08 07:47:32'),(_binary 'òS·\í¸\ÇK¾øH pı{','prompting-user','2025-11-06 08:11:01','2025-11-06 08:11:01');
/*!40000 ALTER TABLE `strategy_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `test_chunk`
--

LOCK TABLES `test_chunk` WRITE;
/*!40000 ALTER TABLE `test_chunk` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_chunk` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `test_collection`
--

LOCK TABLES `test_collection` WRITE;
/*!40000 ALTER TABLE `test_collection` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_collection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `test_file`
--

LOCK TABLES `test_file` WRITE;
/*!40000 ALTER TABLE `test_file` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_file` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (_binary '`[°_ºH,µ÷X\Zƒz','2025-11-14 16:19:26.495760','2025-11-14 16:19:26.495760',NULL,0,'dev@hebees.com','íˆë¹„ìŠ¤íŒ€','$2a$10$A/lVMfkcax14xcaQ8/v5qut/uKF0FBRKkn3sd6RWVFQHzjf6zCv2e','1231212312',_binary '‹D¿†öGc±ˆs*c2¼‚'),(_binary 'I÷\Ø\à\ŞgGÍ“?f´ss„','2025-11-04 00:16:30.130801','2025-11-04 00:16:30.130801',NULL,0,'hebees@naver.com','íˆë¹„ìŠ¤','$2a$10$GkqDZ4Hv.Y5U0UuJ.XV5AOhJ6OEKftfz9K.iG0rIWH6bxTK/GW9Nq','1192182918',_binary '\É\ÚuFQ€I±\ã2\n¯‘KJ'),(_binary '\\†\×òveKFc±\0ü,»\é','2025-11-14 17:24:29.930930','2025-11-14 17:24:29.930930',NULL,0,'test@test.com','í…ŒìŠ¤íŠ¸','$2a$10$2fj33h8Nyk7sK0Gj4DMkm.Z2Dcnvqt4Faxe2FR3sNp//Utu6y2Zk.','1234567890',_binary '‹D¿†öGc±ˆs*c2¼‚'),(_binary '²&Ê±Ò­I7€\Ö;+iD»¥','2025-11-11 09:39:37.497960','2025-11-11 09:39:37.497960',NULL,2,'user@test.com','testì•ˆê²½ì›','$2a$10$X9gGdcgJFqd2ShN4.2yb6.o99cnhbB8wQ8uWFTHixLwyMHDcYpHpC','1234567890',_binary '‹D¿†öGc±ˆs*c2¼‚');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `user_aggregate_hourly`
--

LOCK TABLES `user_aggregate_hourly` WRITE;
/*!40000 ALTER TABLE `user_aggregate_hourly` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_aggregate_hourly` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `user_role`
--

LOCK TABLES `user_role` WRITE;
/*!40000 ALTER TABLE `user_role` DISABLE KEYS */;
INSERT INTO `user_role` VALUES (_binary 'OnùÁI÷™§×™¤¿','2025-11-03 14:09:05.533541','2025-11-03 14:24:24.385338',4,'EDITOR'),(_binary '‹D¿†öGc±ˆs*c2¼‚','2025-10-29 16:19:55.498272','2025-10-29 16:19:55.498272',1,'USER'),(_binary '—¼­õJo¨\Ë]S{\Ô1—','2025-11-03 14:09:47.236178','2025-11-03 14:09:47.236178',5,'MANAGER'),(_binary '›.	Ï—B~¾Sb¬Œ¨ø˜','2025-11-19 15:14:50.640393','2025-11-19 15:14:50.640393',6,'SSAFY'),(_binary '®I:²÷LC·qœ»\è]½\Í','2025-11-03 14:09:31.054046','2025-11-03 14:09:31.054046',3,'READER'),(_binary '\É\ÚuFQ€I±\ã2\n¯‘KJ','2025-11-03 01:50:41.639520','2025-11-03 01:50:41.639520',2,'ADMIN');
/*!40000 ALTER TABLE `user_role` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-20  2:46:10
