package principal;

import EscribirDatos.GuardarDatos;
import java.util.List;
import leerdatos.ObtenerDatos;
import model.Conserje;
import model.Funcionario;
import model.Trabajador;

public class Principal2 {

    public static void main(String[] args) {
        /*
        Conserje t1 = new Conserje();
        t1.setIdTrabajador(1);
        t1.setNombre("Luis");
        t1.setApellido("Ruiz");
        t1.setAntiguedad(15);
        t1.setHorasTrabajadas(150);

        Funcionario t2 = new Funcionario(2, "Carla", "Roncal", 20, 160);

        System.out.println(t1);
        System.out.println("Sueldo t1: " + t1.sueldo());
        System.out.println(t2);
        System.out.println("Sueldo t2: " + t2.sueldo());
         */
        List<Trabajador> trabajadores_al = ObtenerDatos.leerArchivoCsv();
        double a = 0;
        String b = "";
        String c = "";

        for (Trabajador t : trabajadores_al) {
            if (t instanceof Conserje) {

                b = "Conserje";

                System.out.println(t.getNombre() + " " + t.getApellido() + " " + ((Conserje) t).sueldo());

                String cadena = t.getNombre() + ";" + b + ";" + t.sueldo();

                GuardarDatos.guardarArchivosCsv(cadena, b);
            } else {

                b = "Funcionario";

                System.out.println(t.getNombre() + " " + t.getApellido() + " " + ((Funcionario) t).sueldo());

                String cadena = t.getNombre() + ";" + b + ";" + t.sueldo();

                GuardarDatos.guardarArchivosCsv(cadena, b);
            }

        }

    }
    // System.out.println("El mayor sueldo es: " + c + " " + a + " " + b);

    // GuardarDatos.guardarArchivosCsv(cadena,);
}
