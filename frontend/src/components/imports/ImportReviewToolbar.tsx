// CR-053 (F07): busca, filtro por grupo, edicao em massa e totais da revisao.
//
// O filtro E a selecao: nao existe checkbox de selecao por linha. O bulk atua
// sobre as linhas visiveis E incluidas, e a barra diz esse numero antes de
// aplicar — o checkbox da linha continua significando so "incluir na importacao".
import { useState } from "react";
import { Search, X } from "lucide-react";
import { REVIEW_GROUP_KEYS, type BulkPatch, type ReviewFilter, type ReviewGroupKey } from "../../utils/importReview";
import { formatBRL } from "../../utils/format";
import { inputClass } from "./fieldStyles";

const GROUP_LABELS: Record<ReviewGroupKey, string> = {
  novos: "Novos",
  matches: "Conciliações",
  parcelamentos: "Parceladas",
  ignoradas: "Ignoradas",
  duplicadas: "Duplicadas",
};

export interface ImportReviewToolbarProps {
  filter: ReviewFilter;
  onFilterChange: (filter: ReviewFilter) => void;
  incluidas: number;
  totalTransacoes: number;
  totalIncluidas: number;
  alvoIds: string[];
  totalAlvo: number;
  visiveis: number;
  categorias: Record<string, string[]>;
  metodosPagamento: string[];
  // Alvo: as linhas visiveis E incluidas
  onBulkApply: (patch: BulkPatch) => void;
  // Alvo: as visiveis menos as duplicadas (ver bulkIncludeTargetIds)
  onBulkIncluir: (incluida: boolean) => void;
}

export default function ImportReviewToolbar({
  filter,
  onFilterChange,
  incluidas,
  totalTransacoes,
  totalIncluidas,
  alvoIds,
  totalAlvo,
  visiveis,
  categorias,
  metodosPagamento,
  onBulkApply,
  onBulkIncluir,
}: ImportReviewToolbarProps) {
  const [categoria, setCategoria] = useState("");
  const [subcategoria, setSubcategoria] = useState("");
  const [metodo, setMetodo] = useState("");

  const subcategorias = categoria ? categorias[categoria] ?? [] : [];
  const alvo = alvoIds.length;
  // Categoria sozinha nunca e valida: o par e obrigatorio no gasto diario e, no
  // parcelado, categoria sem subcategoria invalida uma linha que era valida com
  // as duas vazias. Entao so habilita quando o par esta completo.
  const parIncompleto = categoria !== "" && subcategoria === "";
  const temPatch = (categoria !== "" && subcategoria !== "") || metodo !== "";

  function toggleGrupo(key: ReviewGroupKey) {
    const ativos = filter.grupos.includes(key)
      ? filter.grupos.filter((g) => g !== key)
      : [...filter.grupos, key];
    onFilterChange({ ...filter, grupos: ativos });
  }

  function handleAplicar() {
    const patch: BulkPatch = {};
    if (categoria && subcategoria) {
      patch.categoria = categoria;
      patch.subcategoria = subcategoria;
    }
    if (metodo) patch.metodoPagamento = metodo;
    onBulkApply(patch);
    setCategoria("");
    setSubcategoria("");
    setMetodo("");
  }

  return (
    <div className="bg-surface rounded-2xl shadow-sm border border-slate-100/80 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
          <input
            type="text"
            value={filter.query}
            onChange={(e) => onFilterChange({ ...filter, query: e.target.value })}
            placeholder="Buscar por descrição..."
            aria-label="Buscar transações"
            className={`${inputClass} pl-9`}
          />
          {filter.query && (
            <button
              type="button"
              onClick={() => onFilterChange({ ...filter, query: "" })}
              aria-label="Limpar busca"
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md
                text-text-muted hover:bg-slate-100 transition-colors duration-100"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <p className="text-sm font-semibold text-text-muted">
          {incluidas} de {totalTransacoes} incluídas ·{" "}
          <span className="text-text font-bold tabular-nums">{formatBRL(totalIncluidas)}</span>
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {REVIEW_GROUP_KEYS.map((key) => {
          const ativo = filter.grupos.includes(key);
          return (
            <button
              key={key}
              type="button"
              onClick={() => toggleGrupo(key)}
              aria-pressed={ativo}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors duration-100
                ${ativo
                  ? "bg-primary text-white border-primary"
                  : "bg-white text-text-muted border-border hover:bg-slate-50"}`}
            >
              {GROUP_LABELS[key]}
            </button>
          );
        })}
      </div>

      <div className="px-3 sm:px-4 py-3 bg-primary-50 border border-primary-light rounded-xl space-y-3 animate-fade-in-up">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span className="text-sm font-semibold text-primary">
            {alvo} {alvo === 1 ? "linha visível e incluída" : "linhas visíveis e incluídas"}
          </span>
          <span className="text-sm font-bold text-text tabular-nums">{formatBRL(totalAlvo)}</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label className="block">
            <span className="text-xs font-semibold text-text-muted">Categoria</span>
            <select
              value={categoria}
              onChange={(e) => {
                setCategoria(e.target.value);
                setSubcategoria("");
              }}
              className={inputClass}
            >
              <option value="">Não alterar</option>
              {Object.keys(categorias).map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-text-muted">Subcategoria</span>
            <select
              value={subcategoria}
              onChange={(e) => setSubcategoria(e.target.value)}
              disabled={!categoria}
              className={inputClass}
            >
              <option value="">Selecione...</option>
              {subcategorias.map((sub) => (
                <option key={sub} value={sub}>{sub}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-text-muted">Método</span>
            <select
              value={metodo}
              onChange={(e) => setMetodo(e.target.value)}
              className={inputClass}
            >
              <option value="">Não alterar</option>
              {metodosPagamento.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleAplicar}
            disabled={alvo === 0 || !temPatch}
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold
              hover:bg-primary-hover active:scale-[0.98] transition-all duration-150
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Aplicar a {alvo} {alvo === 1 ? "linha" : "linhas"}
          </button>
          {parIncompleto && (
            <p className="w-full text-xs text-text-muted">
              Escolha também a subcategoria — categoria sozinha deixaria as linhas inválidas.
            </p>
          )}
          <button
            type="button"
            onClick={() => onBulkApply({ acao: "criar_gasto_diario" })}
            disabled={alvo === 0}
            className="px-4 py-2 text-sm font-semibold text-primary border border-primary-light
              rounded-lg hover:bg-primary/10 transition-colors duration-100 disabled:opacity-40"
          >
            Tratar como novo gasto diário
          </button>
          <button
            type="button"
            onClick={() => onBulkIncluir(true)}
            disabled={visiveis === 0}
            className="px-4 py-2 text-sm font-semibold text-primary border border-primary-light
              rounded-lg hover:bg-primary/10 transition-colors duration-100 disabled:opacity-40"
          >
            Marcar as {visiveis} visíveis
          </button>
          <button
            type="button"
            onClick={() => onBulkIncluir(false)}
            disabled={alvo === 0}
            className="px-4 py-2 text-sm font-semibold text-text-muted border border-border
              rounded-lg hover:bg-slate-50 transition-colors duration-100 disabled:opacity-40"
          >
            Desmarcar as visíveis
          </button>
        </div>
      </div>
    </div>
  );
}
