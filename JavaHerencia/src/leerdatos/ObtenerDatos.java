package leerdatos;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import model.Conserje;
import model.Funcionario;
import model.Trabajador;

public class ObtenerDatos {

    //DEVUELVE UNA COLECCCION DE OBJETOS DE TIPO TRABAJADOR
    public static List<Trabajador> leerArchivoCsv() {

        List<Trabajador> trabajadores_al = new ArrayList<>();

        File f;
        FileReader fr;
        BufferedReader br;

        String fila = ""; //GUARDAR CADA FILA LEIDA DEL ARCHIVO
        String[] parte;

        try {

            f = new File("data/Libro1.csv");
            fr = new FileReader(f);
            br = new BufferedReader(fr);
            int i = 0;
            while ((fila = br.readLine()) != null) {
                if(i != 0){
                System.out.println(fila);
                parte = fila.split(";"); // 1;Luis ["1", "Luis"]
                if (parte[parte.length - 1].equalsIgnoreCase("Conserje")) {
                    Conserje c = new Conserje(Integer.parseInt(parte[0]), parte[1], parte[2],Integer.parseInt(parte[3]), Integer.parseInt(parte[4]));
                    
                    trabajadores_al.add(c);
                            
                    
                } else {
                    Funcionario fu = new Funcionario(Integer.parseInt(parte[0]), parte[1], parte[2],Integer.parseInt(parte[3]), Integer.parseInt(parte[4]));
                    trabajadores_al.add(fu);
                }
            }i++;
            }
            
        } catch (IOException e) {
            System.out.println("Error de lectura" + e);

        }
        return trabajadores_al; 

    }

}
