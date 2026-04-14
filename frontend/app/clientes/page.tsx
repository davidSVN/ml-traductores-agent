import { ClientesTable } from "@/components/clientes/ClientesTable";

export default function ClientesPage() {
  return (
    <div className="p-6">
      <h1 className="text-text-primary text-xl font-bold mb-6">Clientes</h1>
      <ClientesTable />
    </div>
  );
}
