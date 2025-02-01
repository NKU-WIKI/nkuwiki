package Bean;

public class User {
	private String name;
	private int id;
	private storeDisk borrowed;
	private double money;
	
	public User() {
		borrowed=new storeDisk();
	}
	
	public String getName() {
		return name;
	}
	public int getId() {
		return id;
	}
	public double getMoney() {
		return money;
	}
	
	public storeDisk getBorrowed() {
		return borrowed;
	}
	
	public void setName(String name) {
		this.name = name;
	}
	
	public void setId(int id) {
		this.id = id;
	}
	
	public void setMoney(double money) {
		this.money = money;
	}
	
	public void setBorrowed(Disk borrowed) {
		this.borrowed.push(borrowed);
	}
	
	
	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((borrowed == null) ? 0 : borrowed.hashCode());
		result = prime * result + id;
		result = prime * result + ((name == null) ? 0 : name.hashCode());
		return result;
	}
	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		User other = (User) obj;
		
		if (id != other.id)
			return false;
		if (name == null) {
			if (other.name != null)
				return false;
		} else if (!name.equals(other.name))
			return false;
		return true;
	}
	@Override
	public String toString() {
		return "User [name=" + name + ", id=" + id + ", borrowed=" + borrowed + ", money=" + money + "]";
	}
	
	
	
}
