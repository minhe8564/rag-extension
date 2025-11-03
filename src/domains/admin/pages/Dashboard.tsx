import PageHeader from '@/domains/admin/components/dashboard/PageHeader';
import NumberBoard from '@/domains/admin/components/dashboard/NumberBoard';
import ChatbotUsage from '@/domains/admin/components/dashboard/ChatbotUsage';
import MonthlyUsage from '@/domains/admin/components/dashboard/MonthlyUsage';
import AiModel from '@/domains/admin/components/dashboard/AiModel';
import KeywordMap from '@/domains/admin/components/dashboard/KeywordMap';
import ChatbotFlow from '@/domains/admin/components/dashboard/ChatbotRealtime';
import ErrorTypes from '@/domains/admin/components/dashboard/ErrorTypes';
import ChatRoom from '@/domains/admin/components/dashboard/ChatRoom';

export default function Dashboard() {
  return (
    <section>
      <PageHeader />
      <NumberBoard />
      <section className="grid grid-cols-2 gap-4">
        <ChatbotFlow />
        <ChatbotUsage />
      </section>
      <AiModel />
      <MonthlyUsage />
      <KeywordMap />
      <section className="grid grid-cols-2 gap-4">
        <ErrorTypes />
        <ChatRoom />
      </section>
    </section>
  );
}
