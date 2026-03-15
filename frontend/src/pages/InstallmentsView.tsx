import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import {
    ChevronDown,
    ChevronRight,
    CreditCard,
    Calendar,
} from "lucide-react";
import { useMemo, useState } from "react";
import { fetchInstallments } from "../services/api";
import type { InstallmentGroup } from "../types";
import StatusBadge from "../components/StatusBadge";
import ViewSelector from "../components/ViewSelector";
import ProjectionSummaryCards from "../components/installments/ProjectionSummaryCards";
import ProjectionChartToggle from "../components/installments/ProjectionChartToggle";
import { useAuth } from "../hooks/useAuth";
import { useInstallmentProjection } from "../hooks/useInstallmentProjection";
import { getMonthName } from "../utils/date";

// Helper para formatar moeda
const formatMoney = (val: number) =>
    new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
    }).format(val);

export function InstallmentsView() {
    const { user } = useAuth();
    const { data, isLoading, isError, error } = useQuery({
        queryKey: ["installments", user?.id],
        queryFn: fetchInstallments,
        enabled: !!user,
    });

    const projection = useInstallmentProjection();

    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
        {}
    );

    const toggleGroup = (groupName: string) => {
        setExpandedGroups((prev) => ({
            ...prev,
            [groupName]: !prev[groupName],
        }));
    };

    // Separate and sort groups
    const { emAndamento, concluidos } = useMemo(() => {
        if (!data) return { emAndamento: [], concluidos: [] };

        const active = data.groups.filter((g) => g.status_geral === "Em andamento");
        const done = data.groups.filter((g) => g.status_geral === "Concluído");

        // Sort active groups by termination date (soonest first)
        if (projection.data) {
            const projMap = new Map(
                projection.data.parcelas.map((p) => [p.nome, p])
            );
            active.sort((a, b) => {
                const pa = projMap.get(a.nome);
                const pb = projMap.get(b.nome);
                const ra = pa?.parcelas_restantes ?? Infinity;
                const rb = pb?.parcelas_restantes ?? Infinity;
                return ra - rb;
            });
        }

        return { emAndamento: active, concluidos: done };
    }, [data, projection.data]);

    if (isLoading) {
        return (
            <div className="px-4 py-6 sm:p-6 space-y-6 max-w-7xl mx-auto">
                <ViewSelector />
                <div className="flex flex-col justify-center items-center py-24 gap-3">
                    <div className="h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-text-muted text-sm font-medium">Carregando dados...</p>
                </div>
            </div>
        );
    }

    if (isError || !data) {
        return (
            <div className="px-4 py-6 sm:p-6 space-y-6 max-w-7xl mx-auto">
                <ViewSelector />
                <div className="flex flex-col justify-center items-center py-24 gap-2">
                    <p className="text-danger font-bold text-lg">Erro ao carregar parcelamentos</p>
                    <p className="text-text-muted text-sm">{String(error || "Erro desconhecido")}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="px-4 py-6 sm:p-6 space-y-6 max-w-7xl mx-auto">
            <ViewSelector />
            <header className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <CreditCard className="w-8 h-8 text-primary-600" />
                    Compras Parceladas
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                    Visão consolidada de todos os seus parcelamentos e passivos futuros.
                </p>
            </header>

            {/* Seção 1: Cards de Resumo (CR-021) */}
            {projection.data && (
                <ProjectionSummaryCards data={projection.data} />
            )}

            {/* Seção 2: Projeção Visual (CR-021) */}
            {projection.data && projection.data.parcelas.length > 0 && (
                <ProjectionChartToggle data={projection.data} />
            )}

            {/* Seção 3: Lista de Grupos por Status */}
            {data.groups.length === 0 ? (
                <div className="p-8 text-center bg-gray-50 dark:bg-gray-800 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
                    <p className="text-gray-500">Nenhuma compra parcelada encontrada.</p>
                    <p className="text-gray-400 text-sm mt-2">
                        Adicione uma despesa parcelada na aba Gastos Planejados para vê-la aqui.
                    </p>
                </div>
            ) : (
                <div className="space-y-8">
                    {emAndamento.length > 0 && (
                        <GroupSection
                            title="Em Andamento"
                            count={emAndamento.length}
                            groups={emAndamento}
                            expandedGroups={expandedGroups}
                            toggleGroup={toggleGroup}
                            projectionData={projection.data?.parcelas}
                        />
                    )}

                    {concluidos.length > 0 && (
                        <GroupSection
                            title="Concluídos"
                            count={concluidos.length}
                            groups={concluidos}
                            expandedGroups={expandedGroups}
                            toggleGroup={toggleGroup}
                        />
                    )}
                </div>
            )}
        </div>
    );
}

// Helper to get badge style
function getInstallmentBadge(statusBadge: string) {
    switch (statusBadge) {
        case "Encerrando":
            return { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-700 dark:text-amber-400" };
        default:
            return { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-400" };
    }
}

function formatTerminaEm(mesTermino: string | null | undefined): string {
    if (!mesTermino) return "—";
    const [yearStr, monthStr] = mesTermino.split("-");
    const month = parseInt(monthStr, 10);
    return `${getMonthName(month).slice(0, 3)}/${yearStr}`;
}

// Componente de seção (Em Andamento / Concluídos)
function GroupSection({
    title,
    count,
    groups,
    expandedGroups,
    toggleGroup,
    projectionData,
}: {
    title: string;
    count: number;
    groups: InstallmentGroup[];
    expandedGroups: Record<string, boolean>;
    toggleGroup: (name: string) => void;
    projectionData?: Array<{ nome: string; parcelas_restantes: number; mes_termino: string | null; status_badge: string }>;
}) {
    return (
        <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                {title}
                <span className="text-sm font-normal px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                    {count}
                </span>
            </h2>

            {groups.map((group, idx) => {
                const projInfo = projectionData?.find((p) => p.nome === group.nome);
                return (
                    <GroupCard
                        key={`${group.nome}-${idx}`}
                        group={group}
                        isExpanded={!!expandedGroups[group.nome]}
                        onToggle={() => toggleGroup(group.nome)}
                        terminaEm={projInfo?.mes_termino}
                        statusBadge={projInfo?.status_badge}
                    />
                );
            })}
        </div>
    );
}

// Card individual de um grupo de parcelamento
function GroupCard({
    group,
    isExpanded,
    onToggle,
    terminaEm,
    statusBadge,
}: {
    group: InstallmentGroup;
    isExpanded: boolean;
    onToggle: () => void;
    terminaEm?: string | null;
    statusBadge?: string;
}) {
    const badge = statusBadge ? getInstallmentBadge(statusBadge) : null;

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header do Grupo (Clicável) */}
            <div
                onClick={onToggle}
                className="w-full flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
                <div className="flex items-center gap-4">
                    <span className="text-gray-400">
                        {isExpanded ? (
                            <ChevronDown className="w-5 h-5" />
                        ) : (
                            <ChevronRight className="w-5 h-5" />
                        )}
                    </span>
                    <div>
                        <h3 className="text-base font-medium text-gray-900 dark:text-white flex items-center gap-2">
                            {group.nome}
                            <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600">
                                {group.parcela_total}x
                            </span>
                        </h3>
                        <div className="text-sm text-gray-500 flex items-center gap-2 mt-1 flex-wrap">
                            <StatusBadge status={group.status_geral as any} />
                            {badge && statusBadge && (
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${badge.bg} ${badge.text}`}>
                                    {statusBadge}
                                </span>
                            )}
                            {terminaEm && (
                                <span className="text-xs text-gray-400">
                                    Termina em {formatTerminaEm(terminaEm)}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-6 text-right">
                    <div className="hidden sm:block">
                        <p className="text-xs text-gray-400 uppercase font-medium">
                            Pago
                        </p>
                        <p className="text-sm font-medium text-green-600">
                            {formatMoney(group.valor_pago)}
                        </p>
                    </div>
                    <div className="hidden sm:block">
                        <p className="text-xs text-gray-400 uppercase font-medium">
                            Restante
                        </p>
                        <p className="text-sm font-medium text-orange-600">
                            {formatMoney(group.valor_restante)}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-400 uppercase font-medium">
                            Total
                        </p>
                        <p className="text-base font-bold text-gray-900 dark:text-gray-100">
                            {formatMoney(group.valor_total_compra)}
                        </p>
                    </div>
                </div>
            </div>

            {/* Body do Grupo (Tabela de Parcelas) */}
            {isExpanded && (
                <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-4">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-gray-500 uppercase bg-gray-100 dark:bg-gray-700/50">
                                <tr>
                                    <th className="px-4 py-2 rounded-l-lg">Parcela</th>
                                    <th className="px-4 py-2">Vencimento</th>
                                    <th className="px-4 py-2">Valor</th>
                                    <th className="px-4 py-2 rounded-r-lg">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {group.installments.map((inst) => (
                                    <tr
                                        key={inst.id}
                                        className="border-b border-gray-100 dark:border-gray-700/30 last:border-0 hover:bg-gray-100/50 dark:hover:bg-gray-700/30"
                                    >
                                        <td className="px-4 py-2 font-medium">
                                            {inst.parcela_atual}/{inst.parcela_total}
                                        </td>
                                        <td className="px-4 py-2 flex items-center gap-2">
                                            <Calendar className="w-3 h-3 text-gray-400" />
                                            {format(new Date(inst.vencimento), "dd/MM/yyyy")}
                                        </td>
                                        <td className="px-4 py-2">
                                            {formatMoney(inst.valor)}
                                        </td>
                                        <td className="px-4 py-2">
                                            <StatusBadge status={inst.status} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
