import { Sparkles } from "lucide-react";

interface MensagemMotivacionalProps {
  mensagem: string;
}

export default function MensagemMotivacional({ mensagem }: MensagemMotivacionalProps) {
  return (
    <div className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-2xl border border-primary/20 p-5">
      <div className="flex items-start gap-3">
        <Sparkles size={20} className="flex-shrink-0 text-primary mt-0.5" />
        <p className="text-sm text-text leading-relaxed">{mensagem}</p>
      </div>
    </div>
  );
}
