package model;

public class Conserje extends Trabajador {
   private double sueldo;
    public Conserje() {
    }
    
    

    public Conserje(int idTrabajador, String nombre, String apellido, int antiguedad, int horasTrabajadas) {
        super(idTrabajador, nombre, apellido, antiguedad, horasTrabajadas);
    }
    
    
    
 
    
    public double sueldo() {
        this.sueldo = this.getHorasTrabajadas() * 10;
        
        return this.sueldo;
    }
    
    
    
    
    
}
