import { ServiciosTable } from "@/components/servicios/ServiciosTable";
import { EquiposTable } from "@/components/servicios/EquiposTable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ServiciosPage() {
  return (
    <div className="p-6">
      <h1 className="text-text-primary text-xl font-bold mb-6">Servicios y equipos</h1>
      <Tabs defaultValue="servicios">
        <TabsList className="bg-surface mb-4">
          <TabsTrigger value="servicios">Servicios</TabsTrigger>
          <TabsTrigger value="equipos">Equipos</TabsTrigger>
        </TabsList>
        <TabsContent value="servicios">
          <ServiciosTable />
        </TabsContent>
        <TabsContent value="equipos">
          <EquiposTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
