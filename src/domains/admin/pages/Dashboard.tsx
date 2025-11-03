import PageHeader from '@/domains/admin/components/dashboard/PageHeader';
import NumberBoard from '@/domains/admin/components/dashboard/NumberBoard';
import ChatbotUsage from '@/domains/admin/components/dashboard/ChatbotUsage';
import MonthlyUsage from '@/domains/admin/components/dashboard/MonthlyUsage';
import AiModel from '@/domains/admin/components/dashboard/AiModel';
import KeywordMap from '@/domains/admin/components/dashboard/KeywordMap';
export default function Dashboard() {
  return (
    <section>
      <PageHeader />
      <NumberBoard />
      <ChatbotUsage />
      <AiModel />
      <section className="grid grid-cols-2 gap-4">
        <MonthlyUsage />
        <KeywordMap />
      </section>
    </section>
  );
}
