import NumberBoard from '@/domains/admin/components/dashboard/rag/NumberBoard';
import ChatbotUsage from '@/domains/admin/components/dashboard/rag/ChatbotUsage';
import MonthlyUsage from '@/domains/admin/components/dashboard/rag/MonthlyUsage';
import ChatbotFlow from '@/domains/admin/components/dashboard/rag/ChatbotRealtime';
import ErrorTypes from '@/domains/admin/components/dashboard/rag/ErrorTypes';
import ChatRoom from '@/domains/admin/components/dashboard/rag/ChatRoom';
import ModelToken from '@/domains/admin/components/dashboard/rag/ModelToken';
import ModelResponse from '@/domains/admin/components/dashboard/rag/ModelResponse';
import KeywordMap from '@/domains/admin/components/dashboard/rag/KeywordMap';

export default function RagTab() {
  return (
    <>
      <div className="origin-center w-full space-y-2">
        <section className="grid grid-cols-12 gap-2 items-stretch">
          <div className="col-span-6 h-full">
            <NumberBoard />
          </div>
          <div className="col-span-6 h-full">
            <KeywordMap />
          </div>
        </section>

        <section className="grid grid-cols-3 gap-x-2 gap-y-2">
          <ChatbotFlow />
          <ChatbotUsage />
          <ErrorTypes />
        </section>

        <section className="grid grid-cols-3 gap-x-2 gap-y-2">
          <ModelToken />
          <ModelResponse />
          <ChatRoom />
        </section>

        <MonthlyUsage />
      </div>
    </>
  );
}
