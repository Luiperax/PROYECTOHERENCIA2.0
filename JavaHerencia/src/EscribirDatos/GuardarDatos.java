package EscribirDatos;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class GuardarDatos {

    public static void guardarArchivosCsv(String cadena, String TipoFichero) {

        File f;
        FileWriter fw;
        BufferedWriter bw;

        try {
            f = new File("data/" + TipoFichero + ".csv");
            fw = new FileWriter(f,true); // true para grabar más de una vez
            bw = new BufferedWriter(fw);
            bw.write(cadena +"\n"); //Grabar uba cadena de archivos \n para grabar en varias lineas
            bw.flush();
            System.out.println("Grabacion correcta");

        }catch(IOException e){
            System.out.println("Error de escritura");

        }

    }

    public static void guardarArchivosCsv(String cadena) {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

}
