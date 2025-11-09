import ExtractIcon from '@/assets/icons/extract.png';
import ChunkingIcon from '@/assets/icons/chunking.png';
import EmbeddingIcon from '@/assets/icons/embedding.png';
import QueryEmbedIcon from '@/assets/icons/query-embed.png';
import SearchingIcon from '@/assets/icons/searching.png';
import RerankerIcon from '@/assets/icons/reranker.png';
import PromptingIcon from '@/assets/icons/prompting.png';
import GenerationIcon from '@/assets/icons/generation.png';

const size = 36;

export const PipelineIcons = {
  Extract: <img src={ExtractIcon} width={size} height={size} alt="extract" />,
  Chunking: <img src={ChunkingIcon} width={size} height={size} alt="chunking" />,
  Embedding: <img src={EmbeddingIcon} width={size} height={size} alt="embedding" />,
  QueryEmbed: <img src={QueryEmbedIcon} width={size} height={size} alt="query-embed" />,
  Searching: <img src={SearchingIcon} width={size} height={size} alt="searching" />,
  Reranker: <img src={RerankerIcon} width={size} height={size} alt="reranker" />,
  Prompting: <img src={PromptingIcon} width={size} height={size} alt="prompting" />,
  Generation: <img src={GenerationIcon} width={size} height={size} alt="generation" />,
};
