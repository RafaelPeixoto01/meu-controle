import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
    ChevronDown,
    ChevronRight,
    CreditCard,
    DollarSign,
    Calendar,
    CheckCircle2,
    AlertCircle,
    Clock,
} from "lucide-react";
import { useState } from "react";
import { fetchInstallments } from "../services/api";
import { InstallmentGroup } from "../types";
import StatusBadge from "../components/StatusBadge";
import ViewSelector from "../components/ViewSelector";

export function InstallmentsView() {
    const { data, isLoading, isError, error } = useQuery({
        queryKey: ["installments"],
        queryFn: fetchInstallments,
    });

    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
        {}
    );

    const toggleGroup = (groupName: string) => {
        setExpandedGroups((prev) => ({
            ...prev,
            [groupName]: !prev[groupName],
        }));
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (isError || !data) {
        return (
            <div className="p-8 text-center text-red-500">
                <p className="font-bold">Erro ao carregar parcelamentos</p>
                <p className="text-sm text-gray-400 mt-2">{String(error || "Erro desconhecido")}</p>
            </div>
        );
    }

    // Helper para formatar moeda
    const formatMoney = (val: number) =>
        new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL",
        }).format(val);

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto">
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

            {/* Cards de Resumo */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <SummaryCard
                    title="Total Parcelado"
                    value={data.total_gasto}
                    icon={DollarSign}
                    color="text-blue-600"
                    bgColor="bg-blue-50 dark:bg-blue-900/20"
                />
                <SummaryCard
                    title="Já Pago"
                    value={data.total_pago}
                    icon={CheckCircle2}
                    color="text-green-600"
                    bgColor="bg-green-50 dark:bg-green-900/20"
                />
                <SummaryCard
                    title="Pendente"
                    value={data.total_pendente}
                    icon={Clock}
                    color="text-orange-600"
                    bgColor="bg-orange-50 dark:bg-orange-900/20"
                />
                <SummaryCard
                    title="Em Atraso"
                    value={data.total_atrasado}
                    icon={AlertCircle}
                    color="text-red-600"
                    bgColor="bg-red-50 dark:bg-red-900/20"
                />
            </div>

            {/* Lista de Grupos */}
            <div className="space-y-4">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                    Detalhamento por Compra
                </h2>

                {data.groups.length === 0 ? (
                    <div className="p-8 text-center bg-gray-50 dark:bg-gray-800 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
                        <p className="text-gray-500">Nenhuma compra parcelada encontrada.</p>
                    </div>
                ) : (
                    data.groups.map((group, idx) => (
                        <div
                            key={`${group.nome}-${idx}`}
                            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
                        >
                            {/* Header do Grupo (Clicável) */}
                            <div
                                onClick={() => toggleGroup(group.nome)}
                                className="w-full flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                            >
                                <div className="flex items-center gap-4">
                                    <span className="text-gray-400">
                                        {expandedGroups[group.nome] ? (
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
                                        <div className="text-sm text-gray-500 flex items-center gap-2 mt-1">
                                            <StatusBadge status={group.status_geral as any} />
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
                            {expandedGroups[group.nome] && (
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
                    ))
                )}
            </div>
        </div>
    );
}

// Componente auxiliar para Card de Resumo
function SummaryCard({
    title,
    value,
    icon: Icon,
    color,
    bgColor,
}: {
    title: string;
    value: number
    icon: any;
    color: string;
    bgColor: string;
}) {
    const formatMoney = (val: number) =>
        new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL",
        }).format(val);

    return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {title}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {formatMoney(value)}
                </p>
            </div>
            <div className={`p-3 rounded-lg ${bgColor}`}>
                <Icon className={`w-6 h-6 ${color}`} />
            </div>
        </div>
    );
}
