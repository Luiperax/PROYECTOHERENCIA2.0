package model;

public class Funcionario extends Trabajador {
     private double sueldo;
    public Funcionario() {
    }
    
    

    public Funcionario(int idTrabajador, String nombre, String apellido, int antiguedad, int horasTrabajadas) {
        super(idTrabajador, nombre, apellido, antiguedad, horasTrabajadas);
    }
    
    
    

    
    public double sueldo() {
        this.sueldo = this.getHorasTrabajadas() * 25;
        
        return this.sueldo;
    }
    
}
