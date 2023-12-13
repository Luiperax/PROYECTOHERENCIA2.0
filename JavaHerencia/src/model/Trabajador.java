package model;

public abstract class Trabajador {
    private int idTrabajador;
    private String nombre;
    private String apellido;
    private int antiguedad;
    private int horasTrabajadas; 
 

    public Trabajador() {
    }

    public Trabajador(int idTrabajador, String nombre, String apellido, int antiguedad, int horasTrabajadas) {
        this.idTrabajador = idTrabajador;
        this.nombre = nombre;
        this.apellido = apellido;
        this.antiguedad = antiguedad;
         this.horasTrabajadas = horasTrabajadas;
    }

    public int getIdTrabajador() {
        return idTrabajador;
    }

    public void setIdTrabajador(int idTrabajador) {
        this.idTrabajador = idTrabajador;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getApellido() {
        return apellido;
    }

    public void setApellido(String apellido) {
        this.apellido = apellido;
    }

    public int getAntiguedad() {
        return antiguedad;
    }

    public void setAntiguedad(int antiguedad) {
        this.antiguedad = antiguedad;
    }

    public int getHorasTrabajadas() {
        return horasTrabajadas;
    }

    public void setHorasTrabajadas(int horasTrabajadas) {
        this.horasTrabajadas = horasTrabajadas;
    }
    


    @Override
    public String toString() {
        return "Trabajador{" + "idTrabajador=" + idTrabajador + ", nombre=" + nombre + ", apellido=" + apellido + ", antiguedad=" + antiguedad + ", horasTrabajadas=" + horasTrabajadas + '}';
    }

public abstract double sueldo();
    
    
    
    
    
    
    
    
}
