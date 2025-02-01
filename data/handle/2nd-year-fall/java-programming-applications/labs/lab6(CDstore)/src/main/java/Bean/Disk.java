package Bean;
public class Disk {
	private String name;
	private double money;
	private int num;
	
	public String getName() {
		return name;
	}
	public double getMoney() {
		return money;
	}
	public int getNum() {
		return num;
	}
	
	public void setName(String name) {
		this.name = name;
	}
	
	public void setMoney(double money) {
		this.money = money;
	}
	
	public void setNum(int num) {
		this.num = num;
	}
	
	@Override
	public String toString() {
		return "Disk [name=" + name + ", money=" + money + ", num=" + num + "]";
	}
	
	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		long temp;
		temp = Double.doubleToLongBits(money);
		result = prime * result + (int) (temp ^ (temp >>> 32));
		result = prime * result + ((name == null) ? 0 : name.hashCode());
		result = prime * result + num;
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
		Disk other = (Disk) obj;
		
		if (name == null) {
			if (other.name != null)
				return false;
		} else if (!name.equals(other.name))
			return false;
		
		return true;
	}
}